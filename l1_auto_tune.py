import time
import json
import requests

# This loads the TestCenter library.
from StcPython import StcPython

# This loads the AN/LT Transceiver Tune library.
from l1_tune_alg import L1Tune, L1TuneRough

print("Loading TestCenter library ... ", end="", flush=True)
stc = StcPython()
print("Done")

#########################################################################################

# port1_location is to tune
g_port1_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/17"
g_port2_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/25"
g_pg_rx_mode = "DAC"
g_resultdbid = ""
g_iqserviceurl = ""

g_hport1 = None
g_hport2 = None
g_lane_count = 0

g_tune_rough_final = {}
g_tune_final = {}
#########################################################################################

DEFAULT_TIMESERIES_RETENTION_MINS = '360'  # 6 HOURS
def config_result_profile(stc, ts_retention_mins=None):
    """
    Configure the STC LabServer session orion-res result profile.

    Setting the result profile is required to store results in the orion-res database.

    :param obj stc: Instance of an STC LabServer session.
    :param int ts_retention_mins:  Number of minutes to retain orion-res data for.
    :return: None
    :raises Exception: resultdimensionproviderregistry should already exist.
    """

    sel_profile = None
    provider_reg = None
    for child in stc.get('system1', 'children').split():
        if "spirent.results.enhancedresultsselectorprofile" in child:
            sel_profile = child
        elif "spirent.results.resultdimensionproviderregistry" in child:
            provider_reg = child

    if not provider_reg:
        raise Exception("resultdimensionproviderregistry should already exist")

    if not sel_profile:
        sel_profile = stc.create("spirent.results.enhancedresultsselectorprofile", under="system1")

    if ts_retention_mins is None:
        ts_retention_mins = DEFAULT_TIMESERIES_RETENTION_MINS

    stc.config(sel_profile, SubscribeType='ALL',
               EnableLiveDataRetention=True,
               LiveDataRetentionInterval=ts_retention_mins)

def ConfigToDevice(**kwargs):
    global g_hport1
    global g_hport2
    global g_lane_count

    print("   Configuring ... ", end="", flush=True)
    for k, v in kwargs.items():
        i = 1
        while i <= g_lane_count: 
            stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(g_hport1, i), **{k : str(v)})
            #stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(g_hport2, i), **{k : str(v)})
            i += 1
    stc.apply()
    print(" Done")

def GetValueInResult(collumn_name, row_index = 0, **kwargs):
    i = 0
    found = False

    for value in kwargs['columns']:
        if value == collumn_name:
            found = True
            break
        else:
            i += 1
            continue

    if found == True:
        return kwargs['rows'][row_index][i]
    
    return None
    

#########################################################################################

query_l1_port_result_json = {
    "multi_result": {
      "filters": [],
      "groups": [],
      "orders": [
        "view.port_name_str_order ASC",
        "view.port_name_num_order ASC",
        "view.port_name_ip_order ASC",
        "view.port_name_hostname_order ASC",
        "view.port_name_slot_order ASC",
        "view.port_name_port_num_order ASC"
      ],
      "projections": [
        "view.port_name as port_name",
        "view.link_status as link_status",
        "view.an_status as an_status",
        "view.rx_ppm_offset as rx_ppm_offset",
        "view.fpga_temp as fpga_temp",
        "view.module_temp as module_temp",
        "view.module_volt as module_volt"
      ],
      "subqueries": [
        {
          "alias": "view",
          "filters": [
            "l1_port_live_stats$last.is_deleted = false"
          ],
          "groups": [],
          "orders": [],
          "projections": [
            "port.name as port_name",
            "(l1_port_live_stats$last.link_status) as link_status",
            "(l1_port_live_stats$last.an_status) as an_status",
            "(l1_port_live_stats$last.rx_ppm_offset) as rx_ppm_offset",
            "(l1_port_live_stats$last.fpga_temp) as fpga_temp",
            "(l1_port_live_stats$last.module_temp) as module_temp",
            "(l1_port_live_stats$last.module_volt) as module_volt",
            "port.name_str_order as port_name_str_order",
            "port.name_num_order as port_name_num_order",
            "port.name_ip_order as port_name_ip_order",
            "port.name_hostname_order as port_name_hostname_order",
            "port.name_slot_order as port_name_slot_order",
            "port.name_port_num_order as port_name_port_num_order"
          ]
        }
      ]
    }
}

def GetLinkStatusResult():
    global g_resultdbid
    global g_iqserviceurl

    data = {
        "database": {"id": g_resultdbid},
        "mode": "once",
        "definition":query_l1_port_result_json
    }
    
    ret = requests.post(url=g_iqserviceurl+'/queries',json = data)
    ret_dict=ret.json()
    ret_dict=ret_dict['result']
    
    return ret_dict

def VerifyLinkStatusUp():
    time.sleep(10)

    counter = 0
    while counter < 4:
      ret = GetLinkStatusResult()
      link_status = GetValueInResult("link_status", 0, **ret)
      if link_status != None :
          if link_status == "UP":
              return True
      time.sleep(5)
      counter += 1     

    return False

query_l1_port_pcs_result_json = {
    "multi_result": {
      "filters": [],
      "groups": [],
      "orders": [
        "view.port_name_str_order ASC",
        "view.port_name_num_order ASC",
        "view.port_name_ip_order ASC",
        "view.port_name_hostname_order ASC",
        "view.port_name_slot_order ASC",
        "view.port_name_port_num_order ASC"
      ],
      "projections": [
        "view.port_name as port_name",
        "view.cw_count as cw_count",
        "view.rx_fifo_error as rx_fifo_error",
        "view.all_lanes_aligned as all_lanes_aligned",
        "view.fec_lanes_aligned as fec_lanes_aligned",
        "view.tx_local_fault as tx_local_fault",
        "view.rx_local_fault as rx_local_fault",
        "view.rx_remote_fault as rx_remote_fault",
        "view.rx_high_ser as rx_high_ser",
        "view.bip_error as bip_error",
        "view.sync_header_error as sync_header_error",
        "view.post_fec_ser as post_fec_ser",
        "view.pre_fec_ser as pre_fec_ser",
        "view.corrected_cw_total as corrected_cw_total",
        "view.corrected_cw_last_sec as corrected_cw_last_sec",
        "view.corrected_cw_err_sec as corrected_cw_err_sec",
        "view.corrected_cw_per_sec as corrected_cw_per_sec",
        "view.uncorrected_cw_total as uncorrected_cw_total",
        "view.uncorrected_cw_last_sec as uncorrected_cw_last_sec",
        "view.uncorrected_cw_err_sec as uncorrected_cw_err_sec",
        "view.uncorrected_cw_per_sec as uncorrected_cw_per_sec",
        "view.symbol_errors_total as symbol_errors_total",
        "view.symbol_errors_last_sec as symbol_errors_last_sec",
        "view.symbol_errors_err_sec as symbol_errors_err_sec",
        "view.symbol_errors_per_sec as symbol_errors_per_sec",
        "view.code_violations_total as code_violations_total",
        "view.code_violations_last_sec as code_violations_last_sec",
        "view.code_violations_err_sec as code_violations_err_sec",
        "view.code_violations_per_sec as code_violations_per_sec",
        "view.bip_errors_total as bip_errors_total",
        "view.bip_errors_last_sec as bip_errors_last_sec",
        "view.bip_errors_err_sec as bip_errors_err_sec",
        "view.bip_errors_per_sec as bip_errors_per_sec",
        "view.control_code_errors_total as control_code_errors_total",
        "view.control_code_errors_last_sec as control_code_errors_last_sec",
        "view.control_code_errors_err_sec as control_code_errors_err_sec",
        "view.control_code_errors_per_sec as control_code_errors_per_sec",
        "view.sync_header_errors_total as sync_header_errors_total",
        "view.sync_header_errors_last_sec as sync_header_errors_last_sec",
        "view.sync_header_errors_err_sec as sync_header_errors_err_sec",
        "view.sync_header_errors_per_sec as sync_header_errors_per_sec",
        "view.sequence_errors_total as sequence_errors_total",
        "view.sequence_errors_last_sec as sequence_errors_last_sec",
        "view.sequence_errors_err_sec as sequence_errors_err_sec",
        "view.sequence_errors_per_sec as sequence_errors_per_sec"
      ],
      "subqueries": [
        {
          "alias": "view",
          "filters": [
            "l1_port_live_stats$last.is_deleted = false"
          ],
          "groups": [],
          "orders": [],
          "projections": [
            "port.name as port_name",
            "(l1_port_live_stats$last.cw_count) as cw_count",
            "(l1_port_live_stats$last.rx_fifo_error) as rx_fifo_error",
            "(l1_port_live_stats$last.all_lanes_aligned) as all_lanes_aligned",
            "(l1_port_live_stats$last.fec_lanes_aligned) as fec_lanes_aligned",
            "(l1_port_live_stats$last.tx_local_fault) as tx_local_fault",
            "(l1_port_live_stats$last.rx_local_fault) as rx_local_fault",
            "(l1_port_live_stats$last.rx_remote_fault) as rx_remote_fault",
            "(l1_port_live_stats$last.rx_high_ser) as rx_high_ser",
            "(l1_port_live_stats$last.bip_error) as bip_error",
            "(l1_port_live_stats$last.sync_header_error) as sync_header_error",
            "(l1_port_live_stats$last.post_fec_ser) as post_fec_ser",
            "(l1_port_live_stats$last.pre_fec_ser) as pre_fec_ser",
            "(l1_port_live_stats$last.corrected_cw_total) as corrected_cw_total",
            "(l1_port_live_stats$last.corrected_cw_last_sec) as corrected_cw_last_sec",
            "(l1_port_live_stats$last.corrected_cw_err_sec) as corrected_cw_err_sec",
            "(l1_port_live_stats$last.corrected_cw_per_sec) as corrected_cw_per_sec",
            "(l1_port_live_stats$last.uncorrected_cw_total) as uncorrected_cw_total",
            "(l1_port_live_stats$last.uncorrected_cw_last_sec) as uncorrected_cw_last_sec",
            "(l1_port_live_stats$last.uncorrected_cw_err_sec) as uncorrected_cw_err_sec",
            "(l1_port_live_stats$last.uncorrected_cw_per_sec) as uncorrected_cw_per_sec",
            "(l1_port_live_stats$last.symbol_errors_total) as symbol_errors_total",
            "(l1_port_live_stats$last.symbol_errors_last_sec) as symbol_errors_last_sec",
            "(l1_port_live_stats$last.symbol_errors_err_sec) as symbol_errors_err_sec",
            "(l1_port_live_stats$last.symbol_errors_per_sec) as symbol_errors_per_sec",
            "(l1_port_live_stats$last.code_violations_total) as code_violations_total",
            "(l1_port_live_stats$last.code_violations_last_sec) as code_violations_last_sec",
            "(l1_port_live_stats$last.code_violations_err_sec) as code_violations_err_sec",
            "(l1_port_live_stats$last.code_violations_per_sec) as code_violations_per_sec",
            "(l1_port_live_stats$last.bip_errors_total) as bip_errors_total",
            "(l1_port_live_stats$last.bip_errors_last_sec) as bip_errors_last_sec",
            "(l1_port_live_stats$last.bip_errors_err_sec) as bip_errors_err_sec",
            "(l1_port_live_stats$last.bip_errors_per_sec) as bip_errors_per_sec",
            "(l1_port_live_stats$last.control_code_errors_total) as control_code_errors_total",
            "(l1_port_live_stats$last.control_code_errors_last_sec) as control_code_errors_last_sec",
            "(l1_port_live_stats$last.control_code_errors_err_sec) as control_code_errors_err_sec",
            "(l1_port_live_stats$last.control_code_errors_per_sec) as control_code_errors_per_sec",
            "(l1_port_live_stats$last.sync_header_errors_total) as sync_header_errors_total",
            "(l1_port_live_stats$last.sync_header_errors_last_sec) as sync_header_errors_last_sec",
            "(l1_port_live_stats$last.sync_header_errors_err_sec) as sync_header_errors_err_sec",
            "(l1_port_live_stats$last.sync_header_errors_per_sec) as sync_header_errors_per_sec",
            "(l1_port_live_stats$last.sequence_errors_total) as sequence_errors_total",
            "(l1_port_live_stats$last.sequence_errors_last_sec) as sequence_errors_last_sec",
            "(l1_port_live_stats$last.sequence_errors_err_sec) as sequence_errors_err_sec",
            "(l1_port_live_stats$last.sequence_errors_per_sec) as sequence_errors_per_sec",
            "port.name_str_order as port_name_str_order",
            "port.name_num_order as port_name_num_order",
            "port.name_ip_order as port_name_ip_order",
            "port.name_hostname_order as port_name_hostname_order",
            "port.name_slot_order as port_name_slot_order",
            "port.name_port_num_order as port_name_port_num_order"
          ]
        }
      ]
    }
}

def GetPortPcsResult():
    global g_resultdbid
    global g_iqserviceurl

    #results = ""
    #ret = stc.perform("spirent.results.QueryEnhancedResultsValueCommand", ResultQueryJson=json.dumps(query_l1_lane_pcs_result_json), Results=results)
    data = {
        "database": {"id": g_resultdbid},
        "mode": "once",
        "definition":query_l1_port_pcs_result_json
    }
    
    ret = requests.post(url=g_iqserviceurl+'/queries', json = data)
    ret_dict=ret.json()
    ret_dict=ret_dict['result']
    
    return ret_dict

#########################################################################################

def CheckLineQualityForTuneRough():
    global g_hport1
    global g_hport2
    global g_lane_count

    time.sleep(10)
    #stc.perform("L1PcsClearCommand", portlist = g_hport1)
    #stc.perform("L1PcsClearHistoryCommand", portlist = g_hport1)
    stc.perform("ResultsClearAllCommand")
    time.sleep(20)
    ret = GetPortPcsResult()
    ret = GetValueInResult("uncorrected_cw_total", 0, **ret)
    if ret != None:
        uncorrect_cw = int(ret)
        print("uncorrect_cw = %d" %uncorrect_cw)
        return uncorrect_cw == 0

    print("Can't get uncorrect_cw")
    return False

g_line_quality = 0
def GetSymbolErrorsPerSec(port):
    time.sleep(10)
    #stc.perform("L1PcsClearCommand", portlist = port)
    stc.perform("ResultsClearAllCommand")
    time.sleep(20)

    ret = GetPortPcsResult()
    ret = GetValueInResult("symbol_errors_per_sec", 1, **ret)
    if ret != None:
        ret = int(ret)

    return ret

def CheckLineQualityForTune():
    global g_hport1
    global g_hport2
    global g_lane_count
    global g_line_quality

    line_quality = GetSymbolErrorsPerSec(g_hport2)
    offset = abs(line_quality - g_line_quality)
    if offset < int(g_line_quality * 0.1):
        # Deem as jitter
        line_quality = g_line_quality

    print("Cur Line QT: %d, Min Line QT: %d" %(line_quality, g_line_quality))
    if line_quality < g_line_quality:
        g_line_quality = line_quality
        return 1
    elif line_quality > g_line_quality:
        return -1
    
    return 0

#########################################################################################

def SetupTuneEnv(**kwargs):
    global g_port1_location
    global g_port2_location
    global g_pg_rx_mode
    global g_resultdbid
    global g_iqserviceurl
    global g_hport1
    global g_hport2
    global g_lane_count

    if 'port1' in kwargs.keys():
        g_port1_location = kwargs['port1']

    if 'port2' in kwargs.keys():
        g_port2_location = kwargs['port2']

    if 'rxmode' in kwargs.keys():
        g_pg_rx_mode = kwargs['rxmode']

    print("Reserving ports")
    if (g_port1_location == None):
        print("port1 can't be None, exit.")
        exit

    locationlist = []
    locationlist.append(g_port1_location)
    if g_port2_location != None:
        locationlist.append(g_port2_location)
    else:
        g_hport2 = None

    ret = stc.perform("createandreserveports", locationlist = locationlist)

    hportlist = ret["PortList"].split()
    g_hport1 = hportlist[0]
    if g_port2_location != None:
        g_hport2 = hportlist[1]
    print("Reserved ports: %s, location: %s" %(g_hport1, g_port1_location))
    if g_port2_location != None:
        print("Reserved ports: %s, location: %s" %(g_hport2, g_port2_location))

    config_result_profile(stc, None)

    # Check L1 Mode
    if stc.get("%s.l1configgroup" % g_hport1) == None:
        print("%s Not in L1 mode, exit." %g_port1_location)
        exit
    if g_hport2 != None:
        if stc.get("%s.l1configgroup" % g_hport2) == None:
            print("%s Not in L1 mode, exit."  %g_port2_location)
            exit

    print("Get lane_count")
    g_lane_count = int(stc.get("%s.l1configgroup.l1porttxcvrs" % g_hport1, "lanecount"))
    if g_hport2 != None:
        lane_count_port2 = int(stc.get("%s.l1configgroup.l1porttxcvrs" % g_hport2, "lanecount"))
        if g_lane_count != lane_count_port2:
            print("Lane_count of two ports not equal(%d, %d), exit." %(g_lane_count, lane_count_port2))
            exit

    print("lane_count: %d" %(g_lane_count))

    print("Disable AN, set rxmode to %s, set all lane to None ... " %(g_pg_rx_mode), end="", flush=True)
    stc.config("%s.l1configgroup.l1portpcs" %g_hport1, AutoNegotiationEnabled="False")
    stc.config("%s.l1configgroup.l1portpcs" %g_hport2, AutoNegotiationEnabled="False")

    i = 1
    while i <= g_lane_count: 
        stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(g_hport1, i), TxPattern = "None")
        if g_hport2 != None:
            stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(g_hport2, i), TxPattern = "None")
        stc.config("%s.l1configgroup.L1PortTxcvrs.l1lanetxcvrspam4(%d)" %(g_hport1, i), RxMode = g_pg_rx_mode)
        if g_hport2 != None:
            stc.config("%s.l1configgroup.L1PortTxcvrs.l1lanetxcvrspam4(%d)" %(g_hport2, i), RxMode = g_pg_rx_mode)
        i += 1

    stc.apply()
    stc.perform("startenhancedresultstestcommand")
    print("Done")

    # Get IQ ServiceURL
    g_iqserviceurl = stc.get("system1.temevaresultsconfig", "serviceurl")
    print("IQServiceURL: %s" %(g_iqserviceurl))

    # Get IQ DBID
    g_resultdbid = stc.get("project1.testinfo", "resultdbid")
    print("DBID: %s" %(g_resultdbid))


def DoTuneRough():
    global g_pg_rx_mode
    global g_tune_rough_final

    l1_tune_rough = L1TuneRough(None, g_pg_rx_mode)
    case_total = l1_tune_rough.GetCaseTotalMax()
    print("Tune Rough Case Max: %d" %(case_total))

    print("Begin Tune Rough ...")
    counter = 0
    while True:
        config_para = l1_tune_rough.GetNextCase()
        if config_para == None:
            print("Tune Rough finished. Fail")
            break
        print("%3d : " %(counter), end="")
        print(config_para, end="")

        ConfigToDevice(**config_para)

        result = VerifyLinkStatusUp()
        if result == False:
            counter += 1
            continue
        
        print("Link UP")

        result = CheckLineQualityForTuneRough()
        if result == True:
            print("Search finished. Success")
            break
        
        snapshot_name = "L1_Tune_Result_%d_%d_%d_%d_%d" % (config_para['preEmphasis'], config_para['mainTap'], config_para['postEmphasis'], config_para['txCoarseSwing'], config_para['ctle'])
        stc.perform("SaveEnhancedResultsSnapshotCommand", SnapshotName = snapshot_name)
        counter += 1

    g_tune_rough_final = config_para.copy()
    return config_para

def DoTune():
    global g_hport2
    global g_tune_rough_final
    global g_tune_final
    global g_line_quality
    
    g_line_quality = GetSymbolErrorsPerSec(g_hport2)
    print("Min Line QT: %d" %g_line_quality)
    l1_tune = L1Tune(None)
    case_total = l1_tune.GetCaseTotalMax()
    print("Tone Case Max = %d" %(case_total))

    l1_tune.InitCaseBase(**{'conf':g_tune_rough_final})

    print("Begin Tone ...")
    counter = 0
    while True:
        config_para = l1_tune.GetNextCase()
        if config_para['result'] == False:
            print("Finished")
            break
        print("%3d : " %(counter), end="")
        print(config_para['case'], end="")

        ConfigToDevice(**config_para['case'])

        result = VerifyLinkStatusUp()
        if result == False:
            print("Link Down. Finished")
            l1_tune.CaseFeedback(-1)
            counter += 1
            continue

        result = CheckLineQualityForTune()
        l1_tune.CaseFeedback(result)

        snapshot_name = "L1_Tune_Result_%d_%d_%d_%d_%d" % (config_para['preEmphasis'], config_para['mainTap'], config_para['postEmphasis'], config_para['txCoarseSwing'], config_para['ctle'])
        stc.perform("SaveEnhancedResultsSnapshotCommand", SnapshotName = snapshot_name)
        counter += 1

    g_tune_rough_final = l1_tune.GetFinalResult().copy()
    return g_tune_rough_final

if __name__ == "__main__":
    SetupTuneEnv(port1 = g_port1_location, port2 = g_port2_location, rxmode = "DAC")
    g_tune_rough_final = DoTuneRough()
    print("Tune Rough Result: ", end="")
    print(g_tune_rough_final)

    g_tune_final = DoTune()
    print("Tune Result: ", end="")
    print(g_tune_final)