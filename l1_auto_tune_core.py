import sys
import os
import json
import pprint

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

    def __init__(self, file_name):
        self.mDebug = False
        self.mCurConf = {}
        self.mTuneConfDict = {}
        self.mTuneConfFileName = 'tranceiver_para_conf.json'
        self.mCurIndex = 0

        if (file_name != None and len(file_name) > 0):
            self.mTuneConfFileName = file_name

        self.load()    

    def load(self):
        path = os.path.dirname(os.path.abspath(__file__))
        
        with open(os.path.normpath(os.path.join(path, self.mTuneConfFileName)), 'r') as fid:
            self.mTuneConfDict = json.load(fid)['Tune']

    def GetCaseTotalMax(self):
        result = 1
        for value in self.mTuneConfDict.values():
            count = (value['range'][self.RangeIndexDef.end] - value['range'][self.RangeIndexDef.begin] + 1) / value['range'][self.RangeIndexDef.step]
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
            ret['case'] = self.mCurConf.copy()
            ret['case'][k] = self.mTuneConfDict[k]['cur']

        print("L1Tune - GetNextCase:")
        pp.pprint(ret)

        return ret   

     # API
    def GetCaseTuned(self):
        return self.mCurConf

Transceiver_Base_Default = {
    'conf' : {
        'preEmphasis' : -2,
        'mainTap' : 13,
        'postEmphasis' : -2,
        'txCoarseSwing': 4,
        'ctle' : 4
    },
}

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2)

    l1_tone = L1Tune(None)
    l1_tone.mDebug = True
    case_total = l1_tone.GetCaseTotalMax()
    l1_tone.InitCaseBase(**Transceiver_Base_Default)
    pp.pprint(Transceiver_Base_Default)

    offset_list = [0, 1, 1, -1, 1, -1, 1, 1, -1, 1, 0, 1, -1, 1, -1, 1, 1, 1, -1, 0]
    i = 0

    for offset in offset_list:
        i = i + 1
        print("%d:" %(i))
        case = l1_tone.GetNextCase()
        if case['result'] == False:
            print("Finished")
            break

        print("quality_cur: ", end="")
        print("quality_fb: ", end="")
        pp.pprint({'offset' : offset})
        # run testing ...
        l1_tone.CaseFeedback(offset)

    tune_result = l1_tone.GetCaseTuned()
    print("\nTuned Result:")
    pp.pprint(tune_result)
    sys.exit(0)