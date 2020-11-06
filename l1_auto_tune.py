import time
import json

# This loads the TestCenter library.
from StcPython import StcPython

# This loads the AN/LT Transceiver Tune library.
from l1_auto_tune_core import L1Tune
from l1_auto_search_core import L1Search

print("Loading TestCenter library ... ", end="", flush=True)
stc = StcPython()
print("Done")

#########################################################################################

port1_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/17"
#port2_location = "//neb-nickluong-01.calenglab.spirentcom.com/1/9"
pg_rx_mode = "DAC"

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
    print("   Configuring ... ", end="", flush=True)
    for k, v in kwargs.items():
        i = 1
        while i <= lane_count_port1: 
            stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(hport1, i), **{k : str(v)})
            #stc.config("%s.l1configgroup.l1porttxcvrs.l1Lanetxcvrspam4(%d)" %(hport2, i), **{k : str(v)})
            i += 1
    stc.apply()
    print(" Done")

def CheckResult():
    return False

#########################################################################################

print("Reserving ports")
ret = stc.perform("createandreserveports", locationlist=[port1_location])

hportlist = ret["PortList"].split()
hport1 = hportlist[0]
#hport2 = hportlist[1]
print("Reserved ports: %s, location: %s" %(hport1, port1_location))

config_result_profile(stc, None)

# Check L1 Mode
if stc.get("%s.l1configgroup" % hport1) == None:
    print("Not in L1 mode, exit.")
    exit

print("Get lane_count")
lane_count_port1 = int(stc.get("%s.l1configgroup.l1porttxcvrs" % hport1, "lanecount"))
'''
lane_count_port2 = int(stc.get("%s.l1configgroup.l1porttxcvrs" % hport2, "lanecount"))
if lane_count_port1 != lane_count_port2:
    print("Lane_count of two ports not equal, exit.")
    exit
'''    
print("lane_count = %d" %(lane_count_port1))

print("Disable AN, set rxmode to %s, set all lane to PRBS7 ... " %(pg_rx_mode), end="", flush=True)
stc.config("%s.l1configgroup.l1portpcs" %hport1, AutoNegotiationEnabled="False")
#stc.config("%s.l1configgroup.l1portpcs" %hport2, AutoNegotiationEnabled="False")

i = 1
while i <= lane_count_port1: 
    stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(hport1, i), TxPattern = "PRBS7")
    #stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(%d)" %(hport2, i), TxPattern = "PRBS7")
    stc.config("%s.l1configgroup.L1PortTxcvrs.l1lanetxcvrspam4(%d)" %(hport1, i), RxMode = pg_rx_mode)
    #stc.config("%s.l1configgroup.L1PortTxcvrs.l1lanetxcvrspam4(%d)" %(hport2, i), RxMode = pg_rx_mode)
    i += 1

stc.apply()
stc.perform("startenhancedresultstestcommand")
print("Done")

# Get IQ DBID
resultDbId = stc.get("project1.testinfo", "resultdbid")
print("DBID = %s" %(resultDbId))

print("Create L1Search")
l1_search = L1Search(None, "DAC")
case_total = l1_search.GetCaseTotalMax()
print("Case max = %d" %(case_total))

print("Begin search ...")
counter = 0
while True:
    config_para = l1_search.GetNextCase()
    if config_para == None:
        print("Search finished. Fail")
        break
    print("%3d : " %(counter), end="")
    print(config_para, end="")

    ConfigToDevice(**config_para)

    result = CheckResult()
    if result == True:
        print("Search finished. Success")
        break

    counter += 1









query_json = {
  "definition": {
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
        "view.link_status as link_status"
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
            "(l1_port_live_stats$last.rx_ppm_offset) as rx_ppm_offset",
            "(l1_port_live_stats$last.fpga_temp) as fpga_temp",
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
}

expect_json = {
  "columns": [
    "link_status"
  ],
  "rows": [
    [
      "ERROR"
    ],
    [
      "UP"
    ]
  ]
}

ret = stc.perform("spirent.results.VerifyEnhancedResultsValueCommand", ResultQueryJson=json.dumps(query_json), ExpectedResultJson=json.dumps(expect_json))



