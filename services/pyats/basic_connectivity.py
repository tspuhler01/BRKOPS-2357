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
import requests
requests.packages.urllib3.disable_warnings()

class CommonSetup(aetest.CommonSetup):
    
    @aetest.subsection
    def connect(self, testbed):
        for device in testbed:
            if device.type == "C8000V":
                device.connect(init_config_commands=[])

class Testcase(aetest.Testcase):

    @aetest.test
    def basic_connectivity(self, testbed, steps):
        switches = []
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
            
            if device.type == "C9KV-UADP-8P":
                switch = {}
                switch["name"] = device.name
                switch["ip"] = str(device.connections.cli.ip)
                switches.append(switch)

        for device_name in testbed.devices:
            device = testbed.devices[device_name]
            
            if device.type == "C8000V":
                with steps.start("Checking CDP", continue_=True) as step_cdp:
                    if "Total cdp entries displayed : 0" in device.execute(f"show cdp neighbor GigabitEthernet2 detail"):
                        step_cdp.failed("No CDP neighbors found")
                    cdp = device.parse("show cdp neighbor GigabitEthernet2 detail")
                    
                    with step_cdp.start("Check if switch is neighbor", continue_=True) as step_neighbor:
                        for value in cdp["index"].values():
                            if value["device_id"] == "cat9000v":
                                step_neighbor.passed("Switch found")                  
                    
                        step_neighbor.failed("Switch not found")

                    with step_cdp.start("Check if switch has correct IP", continue_=True) as step_ip:
                        for switch in switches:
                            for value in cdp["index"].values():
                                if switch["ip"] in value["management_addresses"]:
                                    step_ip.passed(f"Switch has correct ip")
                            
                            step_ip.failed("Correct IP not found")

                with steps.start("Checking IP connectivity to switch", continue_=True) as step_ping:
                    for switch in switches:
                        ping = device.parse(f"ping vrf 99 {switch['ip']}") 
                        if ping["ping"]["statistics"]["success_rate_percent"] <= 80:
                            step_ping.failed("Check connectivity")
                                
class CommonCleanup(aetest.CommonCleanup):
    
    @aetest.subsection
    def disconnect(self,testbed):
        for device in testbed:
            device.disconnect()        
