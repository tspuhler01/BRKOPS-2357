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

class CommonSetup(aetest.CommonSetup):
    
    @aetest.subsection
    def connect(self, testbed):
        for device in testbed:
            device.connect(init_config_commands=[])

class Testcase(aetest.Testcase):

    @aetest.test
    def router_vrf(self, testbed, steps):        
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C8000V":
                vrf = device.learn("vrf")

                with open(f"/var/baseline/base-vrf_{device.name}.json", 'w') as file:
                    json.dump(vrf.to_dict(), file, indent=4)
    
    @aetest.test
    def switch_vlan(self, testbed, steps):
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C9KV-UADP-8P":
                vlan = device.learn("vlan")

                with open(f"/var/baseline/base-vlan_{device.name}.json", 'w') as file:
                    json.dump(vlan.to_dict(), file, indent=4)
                                
class CommonCleanup(aetest.CommonCleanup):
    
    @aetest.subsection
    def disconnect(self,testbed):
        for device in testbed:
            device.disconnect()        
