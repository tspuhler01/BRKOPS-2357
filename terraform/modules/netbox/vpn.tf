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
  vpn2sites_tmp = flatten([
    for vpn in var.vpns : [
      for site in var.sites : 
        contains(vpn.sites, site.type) ? {
          site_name        = site.name,
          site_id          = site.id,
          site_type        = site.type
          vpn_name         = vpn.name,
          vpn_id           = vpn.id
          router           = site.router
          switches         = site.switches
          switch_interface = "GigabitEthernet1/0/${2 + index(var.vpns, vpn)}"
        } : null
    ]
  ])
  vpn2sites = flatten([
      for site in local.vpn2sites_tmp : {
          vpn_id           = site.vpn_id
          vpn_name         = site.vpn_name
          site_id          = site.site_id
          site_name        = site.site_name
          site_type        = site.site_type
          router           = site.router
          switches         = site.switches
          switch_interface = site.switch_interface
        } if site != null
    ])

  vpn2router = flatten([
    for site in local.vpn2sites : [
      for router in site.router : {
        router    = router
        count     = index(site.router, router) + 1
        vpn_id    = site.vpn_id
        vpn_name  = site.vpn_name
        site_id   = site.site_id
        site_name = site.site_name
        site_type = site.site_type
      }
    ]
  ])

  vpn2switch = flatten([
    for site in local.vpn2sites : [
      for switch in site.switches : {
        switch    = switch
        vpn_id    = site.vpn_id
        vpn_name  = site.vpn_name
        site_id   = site.site_id
        site_name = site.site_name
        site_type = site.site_type
        interface = site.switch_interface
      }
    ]
  ])
}

resource "netbox_vrf" "vpn" {
  for_each    = {for vrf in var.vpns : vrf.id => vrf }
  name        = each.value.id
  description = each.value.name
  tenant_id   = netbox_tenant.brkops2357.id
}

resource "netbox_vlan" "vlan" {
  depends_on = [ netbox_vrf.vpn ]
  for_each   = {for vrf in var.vpns : vrf.id => vrf }
  name       = each.value.name
  vid        = each.value.id
  tenant_id  = netbox_tenant.brkops2357.id
}

resource "netbox_prefix" "vpn_prefix" {
  depends_on  = [ netbox_vrf.vpn ]
  for_each    = {for vrf in var.vpns : vrf.id => vrf }
  prefix      = "10.${each.value.id}.0.0/16"
  status      = "active"
  description = "${each.value.name} networks"
  tenant_id   = netbox_tenant.brkops2357.id
  vrf_id      = netbox_vrf.vpn[each.value.id].id
}

resource "netbox_prefix" "vpn_site_prefix" {
  depends_on  = [ netbox_vrf.vpn ]
  for_each    = {for site in local.vpn2sites : "${site.site_id}_${site.vpn_id}" => site }
  prefix      = "10.${each.value.vpn_id}.${each.value.site_id}.0/24"
  status      = "active"
  description = "${each.value.vpn_name} ${each.value.site_name}"
  tenant_id   = netbox_tenant.brkops2357.id
  vrf_id      = netbox_vrf.vpn[each.value.vpn_id].id
  site_id     = netbox_site.site[each.value.site_id].id
  vlan_id     = netbox_vlan.vlan[each.value.vpn_id].id
}

resource "netbox_device_interface" "router_vpn_intf" {
  depends_on                 = [ netbox_vrf.vpn ]
  for_each                   = { for router in local.vpn2router : "${router.router}_${router.vpn_id}" => router }
  name                       = "${var.router_lan_interface}.${each.value.vpn_id}"
  device_id                  = netbox_device.router[each.value.router].id
  parent_device_interface_id = netbox_device_interface.router_lan_intf[each.value.router].id
  type                       = "virtual"
  description                = each.value.vpn_name
}

resource "netbox_ip_address" "router_vpn_intf_ip" {
  depends_on          = [ netbox_vrf.vpn ]
  for_each            = { for router in local.vpn2router : "${router.router}_${router.vpn_id}" => router }
  ip_address          = "10.${each.value.vpn_id}.${each.value.site_id}.${each.value.count}/24"
  status              = "active"
  device_interface_id = netbox_device_interface.router_vpn_intf[each.key].id
  vrf_id              = netbox_vrf.vpn[each.value.vpn_id].id
  tenant_id           = netbox_tenant.brkops2357.id
}

resource "netbox_device_interface" "switch_vpn_intf" {
  depends_on    = [ netbox_vrf.vpn ]
  for_each      = { for switch in local.vpn2switch : "${switch.switch}_${switch.vpn_id}" => switch }
  name          = each.value.interface
  device_id     = netbox_device.switches[each.value.switch].id
  type          = "1000base-t"
  mode          = "access"
  description   = each.value.vpn_name
  untagged_vlan = netbox_vlan.vlan[each.value.vpn_id].id
}
