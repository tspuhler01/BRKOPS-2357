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

variable netbox_url {
    type = string
}

variable netbox_token {
    type = string
}

variable tenant {
    type = string
}

variable rir {
    type = string
}

variable aggregates {
    type = list(string)
}

variable underlay_prefix {
    type = string
}

variable sdwan_system_ip_prefix {
    type = string
}

variable device_manufacturer {
    type = string
}

variable device_type {
    type = list(string)
}

variable device_roles {
    type = list(string)
}

variable infra_vrf {
    type = string
}

variable infra_prefix {
    type = string
}

variable router_wan_interface {
    type = string
}

variable router_lan_interface {
    type = string
}

variable switch_uplink_interface {
    type = string
}

variable sites {
    type = list(object({
      id       = number
      name     = string
      type     = string
      router   = list(string)
      switches = list(string)
    }))
}

variable vpns {
    type = list(object({
        id    = number
        name  = string
        sites = list(string)
    }))
}