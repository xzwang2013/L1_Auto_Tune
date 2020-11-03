import sys
import os
import json
import pprint

class L1Search():
    
    class RangeIndexDef:
        begin = 0
        end = 1
        step = 2

    def __init__(self, file_name, interface):
        self.mFinshed = False
        self.mCurConf = {}
        self.mSearchConfDict = {}
        self.mSearchConfFileName = 'tranceiver_para_conf.json'
        self.mInterface = interface
        self.mQuality = {}
        if (file_name != None and len(file_name) > 0):
            self.mSearchConfFileName = file_name

        self.load()    

    def load(self):
        path = os.path.dirname(os.path.abspath(__file__))
        
        with open(os.path.normpath(os.path.join(path, self.mSearchConfFileName)), 'r') as fid:
            configDict = json.load(fid)['Search'][self.mInterface]
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

        return ret    

    # API
    def Reset(self):
        self.mFinshed = False
        self.load()

    # API
    def GetCaseTotalMax(self):
        result = 1
        for value in self.mSearchConfDict.values():
            result *= len(value)

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

     # API
    def GetCaseSearched(self):
        return self.mCurConf

if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2)

    l1_search = L1Search(None, "DAC")
    
    case_total = l1_search.GetCaseTotalMax()
    count = 0
    while True:
        config = l1_search.GetNextCase()
        if config == None:
            break
        print("%3d: " %(count), end="")
        print(config)
        count += 1

    sys.exit(0)