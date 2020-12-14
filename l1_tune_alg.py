##############################################################################
#                                                                            #
# Algorithm name: L1Tune and L1TuneRough                                     #
#                                                                            #
# Purpose: The purpose of this algorithm is to find best transceiver         #
# parameters automatically on ethernet ports like 50/100/200/400 gig         #
#                                                                            #
# This algorithm is used to get test cases one by one automatically          #
# with auto optimized prioriry                                               #
#                                                                            #
# 2020/12/01 First Draft Xiaozhou.Wang(Shawn)                                #
#                                                                            #
##############################################################################

import sys
import os
import json
import pprint
from collections import OrderedDict

class L1Tune():
    '''
    mTuneConfDict = {
        "Transceiver_key" : {
            # from config file
            "range" : { ... },
            # dynamic add
            "base" : { ... },
            "cur" : { ... },
            "final" : { ... }
        },    
        ...
    }
    '''
    class RangeIndexDef:
        begin = 0
        end = 1
        step = 2

    def __init__(self, file_name, interface):
        self.mDebug = False
        self.mCurConf = {}
        self.mTuneConfDict = {}
        self.mTuneConfFileName = './transceiver_para_conf.json'
        self.mInterface = interface
        self.mCurIndex = 0

        if (file_name != None and len(file_name) > 0):
            self.mTuneConfFileName = file_name

        self.load()    

    def load(self):
        path = os.path.dirname(os.path.abspath(__file__))
        
        with open(os.path.normpath(os.path.join(path, self.mTuneConfFileName)), 'r') as fid:
            self.mTuneConfDict = json.load(fid, object_pairs_hook=OrderedDict)['Tune'][self.mInterface]

    def GetCaseTotalMax(self):
        result = 1
        for value in self.mTuneConfDict.values():
            count = (value['range'][self.RangeIndexDef.end] - value['range'][self.RangeIndexDef.begin] + 1) / value['range'][self.RangeIndexDef.step] + 1
            result *= count

        return result

    def __GetCurValidKV(self):
        for (k, v) in self.mTuneConfDict.items():
            if v['step'] != 0:
                return True, k, v

        return False, None, None

    def __MoveCurValidKVNext(self):
        while True:
            result, k, v = self.__GetCurValidKV()
            if result == False:
                break
            
            next_value = v['cur'] + v['step']
            v['cur'] = next_value

            if v['cur'] < v['range'][self.RangeIndexDef.begin]:
                v['step'] = 0

                if self.mDebug == True:
                    print("L1Tune - CaseFeedback!(\'%s\')" % (k))
            elif v['cur'] > v['range'][self.RangeIndexDef.end]:
                v['step'] *= -1
                v['cur'] = v['base']

                if self.mDebug == True:
                    print("L1Tune - CaseFeedback<<(\'%s\')" % (k))
            else:
                break 

    def __CaseFeedback(self, offset):
        offset = int(offset)
        result, k, v = self.__GetCurValidKV()
        if result == False:
            return

        if offset > 0:
            v['final'] = v['cur']
            self.mCurConf[k] = v['final']

            if self.mDebug == True:
                print("L1Tune - CaseFeedback(\'%s\' : %d)" % (k, v['cur']))
        elif offset < 0:
            if v['final'] == v['base'] and v['step'] > 0:
                # no better found, revert search
                v['step'] *= -1
                v['cur'] = v['base']

                if self.mDebug == True:
                    print("L1Tune - CaseFeedback<<(\'%s\')" % (k))
            else:
                #better has found ,end this para
                v['step'] = 0

                if self.mDebug == True:
                    print("L1Tune - CaseFeedback!(\'%s\')" % (k))
        else:
            if self.mDebug == True:
                print("L1Tune - CaseFeedback>>(\'%s\')" % (k))

        self.__MoveCurValidKVNext()

    # API
    def InitCaseBase(self, **kwargs):
        self.mCurIndex = 0

        for key in kwargs['conf'].keys():
            if (key in (self.mTuneConfDict.keys())):
                self.mTuneConfDict[key]['base'] = kwargs['conf'][key]
                self.mTuneConfDict[key]['cur'] = kwargs['conf'][key]
                self.mTuneConfDict[key]['final'] = kwargs['conf'][key]
                self.mTuneConfDict[key]['step'] = self.mTuneConfDict[key]['range'][self.RangeIndexDef.step]
                self.mCurConf[key] = kwargs['conf'][key]

        self.__CaseFeedback(0)        

    # API
    def CaseFeedback(self, offset):
        self.__CaseFeedback(offset)

    # API
    def GetNextCase(self):
        ret = dict()
        result, k, v = self.__GetCurValidKV()
        if result == False:
            ret['result'] = False
        else:
            ret['result'] = True
            ret['resultcheck'] = v['resultCheck']
            ret['case'] = self.mCurConf.copy()
            ret['case'][k] = self.mTuneConfDict[k]['cur']

        #print("L1Tune - GetNextCase:")
        #pp.pprint(ret)

        return ret   

    # API
    def GetFinalResult(self):
        return self.mCurConf
        
#########################################################################################

Transceiver_Base_Default = {
    'conf' : {
        'preEmphasis' : -2,
        'mainTap' : 13,
        'postEmphasis' : -2,
        'txCoarseSwing': 4,
        'ctle' : 4
    },
}

class L1TuneRough():
    class RangeIndexDef:
        begin = 0
        end = 1
        step = 2

    def __init__(self, file_name, interface):
        self.mFinshed = False
        self.mCurConf = {}
        self.mSearchConfDict = {}
        self.mSearchConfFileName = './transceiver_para_conf.json'
        self.mInterface = interface
        self.mQuality = {}
        if (file_name != None and len(file_name) > 0):
            self.mSearchConfFileName = file_name

        self.load()    

    def load(self):
        path = os.path.dirname(os.path.abspath(__file__))
        
        with open(os.path.normpath(os.path.join(path, self.mSearchConfFileName)), 'r') as fid:
            configDict = json.load(fid, object_pairs_hook=OrderedDict)['TuneRough'][self.mInterface]
            for k, v in configDict.items():
                self.mSearchConfDict[k] = {}
                self.mSearchConfDict[k]['range'] = self.__ExpandToList(v['range'])
                #Append cunrent index
                self.mSearchConfDict[k]['index'] = 0
                self.mCurConf[k] = self.mSearchConfDict[k]['range'][0]

    def __ExpandToList(self, v):
        ret = []
        begin = v[self.RangeIndexDef.begin]
        end = v[self.RangeIndexDef.end]
        step = v[self.RangeIndexDef.step]

        while begin <= end:
            ret.append(begin)
            begin += step

        ret0 = ret[0:int(len(ret)/2)]
        ret1 = ret[int(len(ret)/2):]
        ret0.reverse()
        ret = ret1
        index = 1
        for value in ret0:
            ret.insert(index, value)
            index += 2

        return ret    

    # API
    def Reset(self):
        self.mFinshed = False
        self.load()

    # API
    def GetCaseTotalMax(self):
        result = 1
        for value in self.mSearchConfDict.values():
            result *= len(value['range'])

        return result

    # API
    def GetNextCase(self):
        if self.mFinshed == True:
            return None

        ret = self.mCurConf.copy()
        to_move = True
        for k, v in self.mSearchConfDict.items():
            if to_move == True:
                v['index'] += 1
                if (v['index'] >= len(v['range'])):
                    v['index'] = 0
                    to_move = True
                else:
                    to_move = False
                self.mCurConf[k] = v['range'][v['index']]    
            else:
                break     
        if to_move == True:
            self.mFinshed = True

        return ret

'''
# Test Auto Tune Rough
if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2)

    l1_tune_rough = L1TuneRough(None, "COPPER")
    
    case_total = l1_tune_rough.GetCaseTotalMax()
    count = 0
    while True:
        config = l1_tune_rough.GetNextCase()
        if config == None:
            break
        print("%3d: " %(count)),
        print(config)
        count += 1

    sys.exit(0)
'''


# Test Auto Tone
if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2)

    l1_tune = L1Tune(None, "COPPER")
    l1_tune.mDebug = True
    case_total = l1_tune.GetCaseTotalMax()
    l1_tune.InitCaseBase(**Transceiver_Base_Default)
    pp.pprint(Transceiver_Base_Default)

    offset_list = [1, -1, 1, -1, 1, -1, 1, 1, -1, 1, 0, 1, -1, 1, -1, 1, 1, 1, -1, 0]
    i = 0

    for offset in offset_list:
        i = i + 1
        print("%d:" %(i))
        case = l1_tune.GetNextCase()
        if case['result'] == False:
            print("Finished")
            break

        print("quality_cur: "),
        print("quality_fb: "),
        pp.pprint({'offset' : offset})
        # run testing ...
        l1_tune.CaseFeedback(offset)

    sys.exit(0)
