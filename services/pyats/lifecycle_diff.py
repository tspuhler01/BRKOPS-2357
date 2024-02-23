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
from genie.utils.diff import Diff
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
                
                with open(f"/var/baseline/base-vrf_{device.name}.json") as file:
                    base_vrf = json.load(file)

                with steps.start(f"Learning VRF configuration on {device.name}", continue_=True) as step_vrf:
                    vrf = device.learn("vrf")

                    with step_vrf.start(f"Comparing to baseline", continue_=True) as step_diff:
                
                        diff = Diff(base_vrf, vrf.to_dict())
                        diff.findDiff()
                        
                        if diff.diffs:
                            step_diff.failed(f"Found configuration drift {diff}")

                diff = Diff(base_vrf, vrf.to_dict())
                diff.findDiff()
                print(diff)
    
    @aetest.test
    def switch_vlan(self, testbed, steps):
        for device_name in testbed.devices:
            device = testbed.devices[device_name]
        
            if device.type == "C9KV-UADP-8P":
                
                with open(f"/var/baseline/base-vlan_{device.name}.json") as file:
                        base_vlan = json.load(file)
                
                with steps.start(f"Learning VLAN configuration on {device.name}", continue_=True) as step_vlan:
                    vlan = device.learn("vlan")

                    with step_vlan.start(f"Comparing to baseline", continue_=True) as step_diff:
                
                        diff = Diff(base_vlan, vlan.to_dict())
                        diff.findDiff()
                        
                        if diff.diffs:
                            step_diff.failed(f"Found configuration drift {diff}")
                                    
class CommonCleanup(aetest.CommonCleanup):
    
    @aetest.subsection
    def disconnect(self,testbed):
        for device in testbed:
            device.disconnect()        
