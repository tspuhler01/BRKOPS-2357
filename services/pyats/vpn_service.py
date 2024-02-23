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
import json
import os

class CommonSetup(aetest.CommonSetup):
    
    @aetest.subsection
    def connect(self, testbed):
        for device in testbed:
            device.connect(init_config_commands=[])

class Testcase(aetest.Testcase):

    @aetest.test
    def router_vrf(self, testbed, steps):
        with open('../terraform/routing/terraform.tfvars.json') as file:
            routing_vars = json.load(file)
        
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C8000V":
                for vpn in routing_vars["vpns"]:
                    vpn_id = vpn["id"]
                    with steps.start(f"Check VRF {vpn_id} on device {device.name}", continue_=True) as step_vrf:        
                        if device.execute(f"show vrf {vpn_id}") == f"% No VRF named {vpn_id}":
                            step_vrf.failed(f"VRF {vpn_id} not configured")
                        
                        vrf = device.parse(f"show vrf {vpn_id}")
                        for router in routing_vars["router"]:
                            if router["variables"]["system_host_name"] == device.name:
                                expected_interface = router["variables"][f"vpn{vpn_id}_interface"]
                                expected_ip = router["variables"][f"vpn{vpn_id}_ipv4_address"]

                                with step_vrf.start(f"Check interface {expected_interface}", continue_=True) as step_interface:
                                    if expected_interface not in vrf["vrf"][str(vpn_id)]["interfaces"]:
                                        step_interface.failed(f"Interface {expected_interface} not configured")
                                    interface_details = device.parse(f"show interface {expected_interface}")
                                
                                    with step_interface.start(f"Check ip {expected_ip}", continue_=True) as step_ip:
                                        if expected_ip not in interface_details[expected_interface]["ipv4"]:
                                            step_ip.failed(f"IP {expected_ip} not configured")

                                    with step_interface.start("Check line-protocol state", continue_=True) as step_state:
                                        if interface_details[expected_interface]["line_protocol"] != "up":
                                            step_state.failed("Line protocol down")                          

    @aetest.test
    def switch_vlan(self, testbed, steps):
        with open('../terraform/switching/terraform.tfvars.json') as file:
            switching_vars = json.load(file)

        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C9KV-UADP-8P":
                for vlan in switching_vars["vlans"]:
                    vlan_id = vlan["id"]
                    vlan_name = vlan["name"]
                    vlan_interfaces = vlan["interfaces"]
                    
                    with steps.start(f"Check VLAN {vlan_id} on device {device.name}", continue_=True) as step_vlan:
                        if device.execute(f"show vlan id {vlan_id}") == f"VLAN id {vlan_id} not found in current VLAN database":
                            step_vlan.failed(f"VLAN {vlan_id} not configured")        
                        
                        vlan = device.parse(f"show vlan id {vlan_id}")
                        with step_vlan.start(f"Check VLAN name {vlan_name}", continue_=True) as step_name:
                            if vlan_name != vlan["vlan-name"]:
                                step_name.failed("VLAN name mismatch")

                        for interface in vlan_interfaces:
                            intf = f"{interface['type']}{interface['name']}"
                            with step_vlan.start(f"Checking {intf}", continue_=True) as step_intf:
                                switchport = device.parse(f"show interface {intf} switchport")
                        
                                with step_intf.start("Check switchport mode", continue_=True) as step_intf_mode:
                                    if switchport[intf]["operational_mode"] != "static access":
                                        step_intf_mode.failed("Not in mode access")

                                with step_intf.start("Check access vlan", continue_=True) as step_intf_vlan:
                                    if switchport[intf]["access_vlan"] != str(vlan_id):
                                        step_intf_vlan.failed("Wrong access vlan")
                                
                                with step_intf.start("Check line-protocol state", continue_=True) as step_intf_state:
                                    interface_details = device.parse(f"show interface {intf}")
                                    if interface_details[intf]["line_protocol"] != "up":
                                        step_intf_state.failed("Line protocol down")

                                with step_intf.start("Check STP forwarding", continue_=True) as step_intf_stp:
                                    stp = device.parse(f"show spanning-tree interface {intf}")
                                    if f"VLAN0{vlan_id}" not in stp["vlan"] or stp["vlan"][f"VLAN0{vlan_id}"]["status"] != "FWD":
                                        step_intf_stp.failed("Spanning-tree not in forwarding state")
                            
                            with step_vlan.start("Check STP forwarding on Uplink", continue_=True) as step_uplink_stp:
                                    uplink = os.getenv("SWITCH_UPLINK")
                                    stp = device.parse(f"show spanning-tree interface {uplink}")
                                    if f"VLAN0{vlan_id}" not in stp["vlan"] or stp["vlan"][f"VLAN0{vlan_id}"]["status"] != "FWD":
                                        step_uplink_stp.failed("Spanning-tree not in forwarding state")
                                    
class CommonCleanup(aetest.CommonCleanup):
    
    @aetest.subsection
    def disconnect(self,testbed):
        for device in testbed:
            device.disconnect()        


