import json
# This loads the TestCenter library.
from StcPython import StcPython
stc = StcPython()

port1_location="//10.109.66.170/1/1"
port2_location="//10.109.66.170/1/2"

print("reserving ports")
ret = stc.perform("createandreserveports", locationlist=[port1_location, port2_location])


hportlist = ret["PortList"].split()


hport1 = hportlist[0]
hport2 = hportlist[1]

print("config port1 lane 0 PRBS TxPattern as PRBS7")
stc.config("%s.l1configgroup.l1portprbs.l1laneprbspam4(1)" % hport1, TxPattern="PRBS7")

stc.apply()




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
print ret["PassFailState"]


