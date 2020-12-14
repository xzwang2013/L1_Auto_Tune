##############################################################################
#                                                                            #
# API name: AutoTune                                                         #
#                                                                            #
# Purpose: The purpose of this AutoTune is to find best transceiver          #
# parameters automatically on ethernet ports like 50/100/200/400             #
# Copper or Fiber gig                                                        #
#                                                                            #
# This API AutoTune is used for stack command                                #
#                                                                            #
# 2020/12/01 First Draft Xiaozhou.Wang(Shawn)                                #
#                                                                            #
##############################################################################

import time
import json
import requests
import sys

# This loads the TestCenter library.
from StcPython import StcPython

# This loads the AN/LT Transceiver Tune library.
from l1_tune_alg import L1Tune, L1TuneRough

print("Loading TestCenter library ... "),
sys.stdout.flush()
stc = StcPython()
print("Done.")

#########################################################################################

# port1_location is to tune
g_port1_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/49"
g_port2_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/57"
#g_port1_location = ""
#g_port2_location = ""

g_interface = "COPPER"
g_resultdbid = ""
g_iqserviceurl = ""

g_port1_name = ""
g_port2_name = ""
g_hport1 = None
g_hport2 = None
g_lane_count = 0
g_stackcommand = False

g_tune_rough_final = {}
g_tune_final = {}

#########################################################################################

def Sleep(time_wait):
     if g_stackcommand == False:
        time.sleep(time_wait)
     else:
        stc.perform("WaitCommand", WaitTime = time_wait)

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

def RefreshTransceiverParaOnGui():
    stc.perform("L1GetTxcvrSettingsCommand", PortList=[g_hport1, g_hport2], LaneNumList=[])

def ConfigToDevice(apply_to_both, **kwargs):
    global g_hport1
    global g_hport2
    global g_lane_count

    print("   Configuring ... "),
    sys.stdout.flush()
    for k, v in kwargs.items():
        i = 1
        while i <= g_lane_count: 
            stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(g_hport1, i), **{k : str(v)})
            if apply_to_both == True:
                stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(g_hport2, i), **{k : str(v)})
            i += 1
    stc.apply()
    print(" Done.")

def GetValueInResult(collumn_name, port_name, **kwargs):
    port_name_collumn_index = 0
    collumn_index = 0
    found = False
    row_index = 0

    for value in kwargs['columns']:
        if value == 'port_name':
            port_name_collumn_index = collumn_index
            collumn_index += 1
        elif value == collumn_name:
            found = True
            break
        else:
            collumn_index += 1
            continue
    
    for value in kwargs['rows']:
        if value[port_name_collumn_index] == port_name:
            break
        else:
            row_index += 1

    if found == True:
        return kwargs['rows'][row_index][collumn_index]
    
    return None

def SaveEnhancedResultsSnapshot(**config_para):
    snapshot_name = "L1_Tune_Result_%d_%d_%d_%d_%d" % (config_para['preEmphasis'], config_para['mainTap'], config_para['postEmphasis'], config_para['txCoarseSwing'], config_para['ctle'])
    stc.perform("SaveEnhancedResultsSnapshotCommand", SnapshotName = snapshot_name)

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
    RefreshTransceiverParaOnGui()

    counter = 0
    while counter < 6:
      Sleep(5)
      ret = GetLinkStatusResult()
      link_status = GetValueInResult("link_status", g_port1_name, **ret)
      if link_status != None :
          if link_status == "UP":
              return True
      Sleep(5)
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

    Sleep(5)
    RefreshTransceiverParaOnGui()
    stc.perform("ResultsClearAllCommand")
    Sleep(10)
    
    ret = GetPortPcsResult()
    ret = GetValueInResult("uncorrected_cw_total", g_port2_name, **ret)
    if ret != None:
        uncorrect_cw = int(ret)
        if g_stackcommand == False:
            print("Current total uncorrect CW is %d." %uncorrect_cw)
        else:
            stc.log("INFO", "L1AutoTune - Current total uncorrect CW is %d." %uncorrect_cw)

        return uncorrect_cw == 0

    if g_stackcommand == False:
        print("Can't get current total uncorrect CW.")
    else:
        stc.log("INFO", "L1AutoTune - Can't get current total uncorrect CW.")

    return False

g_errors_per_sec_src = 0
g_pre_fec_err_rate_src = 0
g_errors_per_sec_dst = 0
g_pre_fec_err_rate_dst = 0
def GetSymbolErrorsInfo(port_name):
    stc.perform("ResultsClearAllCommand")
    Sleep(10)

    result = GetPortPcsResult()
    ret = GetValueInResult("symbol_errors_per_sec", port_name, **result)
    if ret != None:
        ret = int(ret)

    ret1 = GetValueInResult("pre_fec_ser", port_name, **result)

    return ret, ret1

def CheckLineQualityForTune(resultcheck):
    global g_hport1
    global g_hport2
    global g_errors_per_sec_src
    global g_pre_fec_err_rate_src
    global g_errors_per_sec_dst
    global g_pre_fec_err_rate_dst

    if resultcheck == 'dst':
        port_name = g_port2_name
        errors_per_sec_last = g_errors_per_sec_dst
        pre_fec_err_rate_last = g_pre_fec_err_rate_dst
    else:
        port_name = g_port1_name
        errors_per_sec_last = g_errors_per_sec_src
        pre_fec_err_rate_last = g_pre_fec_err_rate_src

    stc.perform("ResultsClearAllCommand")
    Sleep(10)

    counter = 0
    while counter < 4:
        errors_per_sec, pre_fec_err_rate = GetSymbolErrorsInfo(port_name)
        if errors_per_sec == 0 or errors_per_sec > 100000:
            counter += 1
            Sleep(5)
            continue
        else:
            break

    if errors_per_sec == 0 and resultcheck == 'dst':
        return 65535

    offset = abs(errors_per_sec - errors_per_sec_last)
    if offset < int(errors_per_sec_last * 0.1):
        # Deem as jitter
        errors_per_sec = errors_per_sec_last

    if g_stackcommand == False:
        print("Check Result: %s, Cur Current Pre-Fec Rate: %e (%d). History Min Pre-Fec Rate: %e (%d)." %(resultcheck, pre_fec_err_rate, errors_per_sec, pre_fec_err_rate_last, errors_per_sec_last))
    else:
        info = "L1AutoTune - Check Result: %s, Cur Current Pre-Fec Rate: %e (%d). History Min Pre-Fec Rate: %e (%d)." %(str(resultcheck), pre_fec_err_rate, errors_per_sec, pre_fec_err_rate_last, errors_per_sec_last)
        stc.log("INFO", info)

    if errors_per_sec < errors_per_sec_last:
        if resultcheck == 'dst':
            g_errors_per_sec_dst = errors_per_sec
            g_pre_fec_err_rate_dst = pre_fec_err_rate
        else:
            g_errors_per_sec_src = errors_per_sec
            g_pre_fec_err_rate_src = pre_fec_err_rate
        return 1
    elif errors_per_sec > errors_per_sec_last:
        return -1
    
    return 0

#########################################################################################

def SetupTuneEnv(**kwargs):
    global g_port1_location
    global g_port2_location
    global g_interface
    global g_resultdbid
    global g_iqserviceurl
    global g_hport1
    global g_hport2
    global g_lane_count
    global g_stackcommand
    global stc
    global g_port1_name
    global g_port2_name

    if 'stackcommand' in kwargs.keys():
        if kwargs['stackcommand'] == True:
            g_stackcommand = True
            
    if 'rxmode' in kwargs.keys():
        g_interface = kwargs['rxmode']
    
    if g_stackcommand == True:
        g_hport1 = kwargs['port1']
        g_hport2 = kwargs['port2']
    else:
        if 'port1' in kwargs.keys():
            g_port1_location = kwargs['port1']

        if 'port2' in kwargs.keys():
            g_port2_location = kwargs['port2']
        
        print("Reserving ports ...")
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
        print("Reserved ports: %s, location: %s." %(g_hport1, g_port1_location))
        if g_port2_location != None:
            print("Reserved ports: %s, location: %s." %(g_hport2, g_port2_location))

        config_result_profile(stc, None)

    # Get Port Name
    g_port1_name = stc.get(g_hport1, "name")
    g_port2_name = stc.get(g_hport2, "name")

    # Check L1 Mode
    if stc.get("%s.l1configgroup" % g_hport1) == None:
        if g_stackcommand == False:
            print("%s Not in L1 mode, exit." %g_port1_location)
            exit
        else:
            stc.log("WARN", "L1AutoTune - %s isn't in l1 mode, exit." %str(g_port1_location))
            return False

    if g_hport2 != None:
        if stc.get("%s.l1configgroup" % g_hport2) == None:
            if g_stackcommand == False:
                print("%s Not in L1 mode, exit." %g_port2_location)
                exit
            else:
                stc.log("WARN", "L1AutoTune - %s isn't in l1 mode, exit." %str(g_port2_location))
                return False

    # Check rxmode
    rxmode_port1 = stc.get("%s" % g_hport1, "PhyMediaType")
    if g_hport2 != None:
        rxmode_port2 = stc.get("%s" % g_hport2, "PhyMediaType")
        if rxmode_port1 != rxmode_port2:
            if g_stackcommand == False:
                print("Rxmode of two ports are not same(%d, %d), exit." %(rxmode_port1, rxmode_port2))
                exit
            else:
                stc.log("WARN", "L1AutoTune - Rxmode of two ports are not same(%d, %d), exit." %(rxmode_port1, rxmode_port2))
                return False
    g_interface = rxmode_port1
    if g_interface != 'COPPER' and g_interface!= 'FIBER':
        g_interface = 'FIBER'
    if g_stackcommand == False:
        print("PhyMediaType: %s" %g_interface)
    else:
        stc.log("INFO", "L1AutoTune -PhyMediaType: %s" %g_interface)

    # Check lane count
    print("Get lane_count ...")
    g_lane_count = int(stc.get("%s.l1configgroup.l1porttxcvrs" % g_hport1, "lanecount"))
    if g_hport2 != None:
        lane_count_port2 = int(stc.get("%s.l1configgroup.l1porttxcvrs" % g_hport2, "lanecount"))
        if g_lane_count != lane_count_port2:
            if g_stackcommand == False:
                print("Lane_count of two ports not equal(%d, %d), exit." %(g_lane_count, lane_count_port2))
                exit
            else:
                stc.log("WARN", "L1AutoTune - Lane_count of two ports not equal(%d, %d), exit." %(g_lane_count, lane_count_port2))
                return False

    print("lane_count: %d" %(g_lane_count))

    # Disable AN
    if g_stackcommand == False:
        print("Disable AN, set all lane's pattern to None ... "),
        sys.stdout.flush()
    else:
        stc.log("INFO", "L1AutoTune - Disable AN, set all lane's pattern to None ... ")

    stc.config("%s.l1configgroup.l1portpcs" %g_hport1, AutoNegotiationEnabled="False")
    stc.config("%s.l1configgroup.l1portpcs" %g_hport2, AutoNegotiationEnabled="False")

    # Config None Pattern
    i = 1
    while i <= g_lane_count: 
        stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(g_hport1, i), TxPattern = "None")
        if g_hport2 != None:
            stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(g_hport2, i), TxPattern = "None")
        i += 1

    stc.apply()
    stc.perform("startenhancedresultstestcommand")
    print("Done.")

    # Get IQ ServiceURL
    g_iqserviceurl = stc.get("system1.temevaresultsconfig", "serviceurl")
    print("IQServiceURL: %s" %(g_iqserviceurl))

    # Get IQ DBID
    g_resultdbid = stc.get("project1.testinfo", "resultdbid")
    print("DBID: %s" %(g_resultdbid))

    return True

def DoTuneRough():
    global g_interface
    global g_tune_rough_final

    l1_tune_rough = L1TuneRough(None, g_interface)
    case_total = l1_tune_rough.GetCaseTotalMax()
    if g_stackcommand == False:
        print("Tune Rough Case Max: %d." %(case_total))
    else:
        stc.log("INFO", "L1AutoTune - Tune Rough Case Max: %d." %(case_total))

    if g_stackcommand == False:
        print("Begin Tune Rough ...")
    else:
        stc.log("INFO", "L1AutoTune - Begin Tune Rough ...")

    counter = 0
    while True:
        config_para = l1_tune_rough.GetNextCase()
        if config_para == None:
            if g_stackcommand == False:
                print("Tune Rough finished. Fail.")
            else:
                stc.log("INFO", "L1AutoTune - Tune Rough finished, fail.")
            return None

        if g_stackcommand == False:
            print("%3d : " %(counter)),
            print(json.dumps(config_para)),
        else:
            info = "L1AutoTune - %3d : %s" %(counter, json.dumps(config_para))
            stc.log("INFO", info)

        ConfigToDevice(True, **config_para)

        result = VerifyLinkStatusUp()
        if result == False:
            counter += 1
            continue
        
        if g_stackcommand == False:
            print("Link Up.")
        else:
            stc.log("INFO", "L1AutoTune - Link Up.")

        result = CheckLineQualityForTuneRough()
        if result == True:
            if g_stackcommand == False:
                print("Tune Rough Finished Successfully.")
            else:
                stc.log("INFO", "L1AutoTune - Tune Rough Finished Successfully.")
            break
        
        SaveEnhancedResultsSnapshot(**config_para)
        counter += 1

    g_tune_rough_final = config_para.copy()
    return config_para

def DoTune(interface):
    global g_hport2
    global g_tune_rough_final
    global g_tune_final
    global g_errors_per_sec_src
    global g_pre_fec_err_rate_src
    global g_errors_per_sec_dst
    global g_pre_fec_err_rate_dst
    
    g_errors_per_sec_src, g_pre_fec_err_rate_src = GetSymbolErrorsInfo(g_port1_name)
    g_errors_per_sec_dst, g_pre_fec_err_rate_dst = GetSymbolErrorsInfo(g_port2_name)
    if g_stackcommand == False:
        print("Current Src Pre-Fec Rate: %e (%d). Dst Pre-Fec Rate: %e (%d)." %(g_pre_fec_err_rate_src, g_errors_per_sec_src, g_pre_fec_err_rate_dst, g_errors_per_sec_dst))
    else:
        stc.log("INFO", "L1AutoTune - Current Src Pre-Fec Rate: %e (%d). Dst Pre-Fec Rate: %e (%d)." %(g_pre_fec_err_rate_src, g_errors_per_sec_src, g_pre_fec_err_rate_dst, g_errors_per_sec_dst))
    l1_tune = L1Tune(None, interface)

    case_total = l1_tune.GetCaseTotalMax()
    if g_stackcommand == False:
        print("Tune Case Max: %d" %(case_total))
    else:
        stc.log("INFO", "L1AutoTune - Tune Case Max: %d" %(case_total))

    l1_tune.InitCaseBase(**{'conf':g_tune_rough_final})

    if g_stackcommand == False:
        print("Begin Tune ...")
    else:
        stc.log("INFO", "L1AutoTune - Begin Tune ...")

    counter = 0
    while True:
        config_para = l1_tune.GetNextCase()
        if config_para['result'] == False:
            if g_stackcommand == False:
                print("Tune Finished Successfully.")
            else:
                stc.log("INFO", "L1AutoTune - Tune Finished Successfully.")
            break

        if g_stackcommand == False:
            print("%3d : " %(counter)),
            print(json.dumps(config_para['case'])),
        else:
            info = "L1AutoTune - %3d : %s" %(counter, json.dumps(config_para['case']))
            stc.log("INFO", info)

        ConfigToDevice(True, **config_para['case'])
        result = VerifyLinkStatusUp()
        if result == False:
            print("Link Down.")
            l1_tune.CaseFeedback(-1)
        else:
            result = CheckLineQualityForTune(config_para['resultcheck'])
            if result == 65535:
                if g_stackcommand == False:
                    print("Tune Finished, zero CW error.")
                else:
                    stc.log("INFO", "L1AutoTune - Tune Finished, zero CW error.")
                SaveEnhancedResultsSnapshot(**config_para)
                break
            else:
                l1_tune.CaseFeedback(result)

        SaveEnhancedResultsSnapshot(**config_para['case'])
        counter += 1

    g_tune_rough_final = l1_tune.GetFinalResult().copy()
    return g_tune_rough_final

def Reset():
    global g_tune_rough_final
    global g_tune_final
    global g_interface
    global g_resultdbid
    global g_iqserviceurl
    global g_hport1
    global g_hport2
    global g_lane_count

    g_interface = "COPPER"
    g_resultdbid = ""
    g_iqserviceurl = ""

    g_hport1 = None
    g_hport2 = None
    g_lane_count = 0

    g_tune_rough_final = {}
    g_tune_final = {}

def AutoTune(portSrc, portDst):
    global g_tune_rough_final
    global g_tune_final
    global g_errors_per_sec_src
    global g_pre_fec_err_rate_src
    global g_errors_per_sec_dst
    global g_pre_fec_err_rate_dst
    global g_interface

    result = SetupTuneEnv(port1 = portSrc, port2 = portDst, stackcommand = True)
    if result == False:
        if g_stackcommand == False:
            print("Setup tune env fail.")
        else:
            stc.log("INFO", "L1AutoTune - Setup tune env fail.")
        return False

    g_tune_rough_final = DoTuneRough()
    if g_tune_rough_final == None:
        return False

    if g_stackcommand == False:
        print("Tune Rough Para: %s" %json.dumps(g_tune_rough_final))
    else:
        stc.log("INFO", "L1AutoTune - Tune Rough Para: %s" %json.dumps(g_tune_rough_final))

    g_tune_final = DoTune(g_interface)
    ConfigToDevice(True, **g_tune_final)
    RefreshTransceiverParaOnGui()
    stc.perform("ResultsClearAllCommand")

    Sleep(10)
    g_errors_per_sec_src, g_pre_fec_err_rate_src = GetSymbolErrorsInfo(g_port1_name)
    g_errors_per_sec_dst, g_pre_fec_err_rate_dst = GetSymbolErrorsInfo(g_port2_name)
    if g_stackcommand == False:
        print("Final Src Pre-Fec Rate: %e (%d). Dst Pre-Fec Rate: %e (%d)." %(g_pre_fec_err_rate_src, g_errors_per_sec_src, g_pre_fec_err_rate_dst, g_errors_per_sec_dst))
        print("Final Tranceiver Para: %s." %json.dumps(g_tune_final))
    else:
        stc.log("INFO", "L1AutoTune - Final Src Pre-Fec Rate: %e (%d). Dst Pre-Fec Rate: %e (%d)." %(g_pre_fec_err_rate_src, g_errors_per_sec_src, g_pre_fec_err_rate_dst, g_errors_per_sec_dst))
        stc.log("INFO", "L1AutoTune - Final Tranceiver Para: %s." %json.dumps(g_tune_final))
    return True

if __name__ == "__main__":
    SetupTuneEnv(port1 = g_port1_location, port2 = g_port2_location, rxmode = "COPPER")
    g_tune_rough_final = DoTuneRough()
    if g_tune_rough_final == None:
        print("Tune Rough Failed.")
        exit
    else:
        print("Tune Rough Result: %s" %json.dumps(g_tune_rough_final))

    g_tune_final = DoTune(g_interface)
    ConfigToDevice(True, **g_tune_final)
    stc.perform("ResultsClearAllCommand")
    print("Tune Result: %s", json.dumps(g_tune_final))

