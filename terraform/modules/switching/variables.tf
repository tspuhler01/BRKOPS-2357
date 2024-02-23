/*
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
*/

variable tenant {
    type = string
}

variable infra_vrf {
    type = string
}

variable switch_uplink_interface {
    type = string
}

variable switches {
    type = list(map(string))
}

variable vlans {
    type = list(object({
        id         = string
        name       = string
        sites      = list(string)
        interfaces = list(map(string))
    })
    )
}

variable device_roles {
    type = list(string)
}

variable devices {
    type = list(map(string))
}