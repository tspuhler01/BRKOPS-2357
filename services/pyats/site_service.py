"""
Copyright (c) 2024 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from pyats import aetest
from pyats.contrib.creators.netbox import Netbox
from genie import testbed
import os
import json
import requests
requests.packages.urllib3.disable_warnings()
from vmngclient.session import create_vManageSession

class CommonSetup(aetest.CommonSetup):
    
    @aetest.subsection
    def connect(self, testbed):
        for device in testbed:
            device.connect(init_config_commands=[])

class Testcase(aetest.Testcase):

    @aetest.test()
    def router_infra(self, testbed, steps):
        with open('../terraform/routing/terraform.tfvars.json') as file:
            routing_vars = json.load(file)
        infra_vrf = os.getenv("INFRA_VRF")
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C8000V":
                with steps.start("Check infra VRF", continue_=True) as step_infra:
                    if device.execute(f"show vrf {infra_vrf}") == f"% No VRF named {infra_vrf}":
                        step_infra.failed(f"VRF {infra_vrf} not configured")    
                    
                    vrf = device.parse(f"show vrf {infra_vrf}")
                    for router in routing_vars["router"]:
                        if router["variables"]["system_host_name"] == device.name:
                            expected_interface = router["variables"][f"vpn{infra_vrf}_interface"]
                            expected_ip = router["variables"][f"vpn{infra_vrf}_ipv4_address"]
                            
                            with step_infra.start(f"Check interface {expected_interface}", continue_=True) as step_interface:
                                if expected_interface not in vrf["vrf"][str(infra_vrf)]["interfaces"]:
                                    step_interface.failed(f"Interface {expected_interface} not configured")
                                interface_details = device.parse(f"show interface {expected_interface}")
                            
                                with step_interface.start(f"Check ip {expected_ip}", continue_=True) as step_ip:
                                    if expected_ip not in interface_details[expected_interface]["ipv4"]:
                                        step_ip.failed(f"IP {expected_ip} not configured")
                                
                                with step_interface.start("Check line-protocol state", continue_=True) as step_state:
                                    if interface_details[expected_interface]["line_protocol"] != "up":
                                        step_state.failed("Line protocol down")                          

                with steps.start("Check connectivity", continue_=True) as step_connectivity: 
                    with step_connectivity.start("Checking access to internal services") as step_internal:
                        destinations = ["git.its-best.ch", "vmanage.its-best.ch", "dnac.its-best.ch"]
                        for dest in destinations:
                            ping = device.parse(f"ping vrf 99 {dest}") 
                            if ping["ping"]["statistics"]["success_rate_percent"] < 80:
                                step_internal.failed(f"No connectivity to {dest}")
                    with step_connectivity.start("Checking access to internet") as step_external:
                        destinations = ["google.ch", "cisco.com"]
                        for dest in destinations:
                            ping = device.parse(f"ping vrf 99 {dest}") 
                            if ping["ping"]["statistics"]["success_rate_percent"] < 80:
                                step_external.failed(f"No connectivity to {dest}")

                with steps.start("Check if bandwidth > 30M", continue_=True) as step_throughput:
                    vmanage_host = os.getenv("VMANAGE_HOST")
                    vmanage_user = os.getenv("VMANAGE_USER")
                    vmanage_password = os.getenv("VMANAGE_PASSWORD")
                    session = create_vManageSession(url=f"https://{vmanage_host}", username=vmanage_user, password=vmanage_password)
                    devices = session.api.devices.get()
                    dc = devices.filter(hostname="site-01-r01")
                    branch = devices.filter(hostname=device.name)
                    dc_router = dc[0] if dc else None
                    branch_router = branch[0] if branch else None

                    speedtest = session.api.speedtest.speedtest(branch_router, dc_router, test_duration_seconds=15)
                    if speedtest.down_speed < 30:
                        step_throughput.failed("Slower than 30 Mbps")
    
    @aetest.test()           
    def switch_infra(self, testbed, steps):
        infra_vlan = os.getenv("INFRA_VRF")
        uplink = os.getenv("SWITCH_UPLINK")
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C9KV-UADP-8P":
                with steps.start(f"Check VLAN {infra_vlan} on device {device.name}", continue_=True) as step_vlan:
                    if device.execute(f"show vlan id {infra_vlan}") == f"VLAN id {infra_vlan} not found in current VLAN database":
                        step_vlan.failed(f"VLAN {infra_vlan} not configured")        
                    
                    vlan = device.parse(f"show vlan id {infra_vlan}")
                    
                    with step_vlan.start(f"Check VLAN name INFRA", continue_=True) as step_name:
                        if vlan["vlan-name"] != "INFRA":
                            step_name.failed("VLAN name mismatch")
                    
                    with step_vlan.start(f"Checking Uplink {uplink}", continue_=True) as step_intf:
                        switchport = device.parse(f"show interface {uplink} switchport")
                        
                        with step_intf.start("Check switchport mode", continue_=True) as step_intf_mode:
                            if switchport[uplink]["operational_mode"] != "trunk":
                                step_intf_mode.failed("Not in trunk mode")

                        with step_intf.start("Check line-protocol state", continue_=True) as step_intf_state:
                            interface_details = device.parse(f"show interface {uplink}")
                            if interface_details[uplink]["line_protocol"] != "up":
                                step_intf_state.failed("Line protocol down")

                    with step_vlan.start("Check STP forwarding", continue_=True) as step_uplink_stp:  
                        stp = device.parse(f"show spanning-tree interface {uplink}")
                        if f"VLAN00{infra_vlan}" not in stp["vlan"] or stp["vlan"][f"VLAN00{infra_vlan}"]["status"] != "FWD":
                            step_uplink_stp.failed("Spanning-tree not in forwarding state")

                    with step_vlan.start(f"Check SVI VLAN{infra_vlan}", continue_=True) as step_svi:  
                        svi = device.parse(f"show ip interface vlan{infra_vlan}")
                        
                        with step_svi.start("Check oper state", continue_=True) as step_svi_state:
                            if svi[f"Vlan{infra_vlan}"]["oper_status"] != "up":
                                step_svi_state.failed("SVI down")
                        
                        with step_svi.start("Check IP address", continue_=True) as step_svi_ip:
                            device_ip = str(device.connections.cli.ip)                            
                            if svi[f"Vlan{infra_vlan}"]["ipv4"][f"{device_ip}/24"]["ip"] != device_ip:
                                step_svi_ip.failed("SVI has wrong ip")
                              
                with steps.start("Check connectivity", continue_=True) as step_connectivity: 
                    with step_connectivity.start("Checking access to internal services") as step_internal:
                        destinations = ["192.168.99.10"]
                        for dest in destinations:
                            ping = device.parse(f"ping {dest}") 
                            if ping["ping"]["statistics"]["success_rate_percent"] < 80:
                                step_internal.failed(f"No connectivity to {dest}")
                    with step_connectivity.start("Checking access to internet") as step_external:
                        destinations = ["google.ch", "cisco.com"]
                        for dest in destinations:
                            ping = device.parse(f"ping {dest}") 
                            if ping["ping"]["statistics"]["success_rate_percent"] < 80:
                                step_external.failed(f"No connectivity to {dest}")
                                
class CommonCleanup(aetest.CommonCleanup):
    
    @aetest.subsection
    def disconnect(self,testbed):
        for device in testbed:
            device.disconnect()        

