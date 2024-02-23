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

locals {
  
  vlan2switch = flatten([
    for switch in var.switches : [
      for vlan in var.vlans : {
        switch_name     = switch.name
        switch_type     = switch.type
        vlan_id         = vlan.id
        vlan_name       = vlan.name
        vlan_interfaces = vlan.interfaces
        vlan_sites      = vlan.sites
      }
    ]
  ])

  vlan2interface = flatten([
    for vlan in local.vlan2switch : [
      for interface in vlan.vlan_interfaces : {
        switch_name    = vlan.switch_name
        switch_type    = vlan.switch_type
        vlan_id        = vlan.vlan_id
        vlan_name      = vlan.vlan_name
        vlan_sites     = vlan.vlan_sites
        interface_type = interface.type
        interface_name = interface.name
      }
    ]
  ])
}

resource "iosxe_vlan" "branch" {
  depends_on = [ null_resource.onboarding_state ]
  for_each   = { for vlan in local.vlan2switch : "${vlan.switch_name}_${vlan.vlan_id}" => vlan if contains(vlan.vlan_sites, vlan.switch_type) }
  device     = each.value.switch_name
  vlan_id    = each.value.vlan_id
  name       = each.value.vlan_name
  shutdown   = false
}

resource "iosxe_interface_ethernet" "branch_access" {
  depends_on  = [ iosxe_vlan.branch ]
  for_each    = { for interface in local.vlan2interface : "${interface.switch_name}_${interface.interface_name}" => interface if contains(interface.vlan_sites, interface.switch_type)}
  device      = each.value.switch_name
  type        = each.value.interface_type
  name        = each.value.interface_name
  description = each.value.vlan_name
  shutdown    = false
  switchport  = true
}

resource "iosxe_interface_switchport" "branch_access" {
  depends_on  = [ iosxe_interface_ethernet.branch_access ]
  for_each    = { for interface in local.vlan2interface : "${interface.switch_name}_${interface.interface_name}" => interface if contains(interface.vlan_sites, interface.switch_type)}
  device      = each.value.switch_name
  type        = each.value.interface_type
  name        = each.value.interface_name
  mode_access = true
  access_vlan = each.value.vlan_id
}