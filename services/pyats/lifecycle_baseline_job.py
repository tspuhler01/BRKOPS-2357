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

from pyats.contrib.creators.netbox import Netbox
from pyats.easypy import run
from genie import testbed
import os

def main(runtime):
    nb_testbed = Netbox(
        netbox_url = os.getenv("NETBOX_URL"),
        user_token = os.getenv("NETBOX_TOKEN"),
        def_user = os.getenv("IOSXE_USERNAME"),
        def_pass = os.getenv("IOSXE_PASSWORD"),
        verify = False
    )

    tb = nb_testbed._generate()
    devices = testbed.load(tb)
    
    run(testscript="lifecycle_baseline.py", testbed=devices, runtime=runtime,)