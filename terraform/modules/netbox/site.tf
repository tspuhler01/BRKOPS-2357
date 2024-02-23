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
  router = flatten([
    for site in var.sites : [
      for router in site.router : {
        serial    = router
        site_name = site.name
        site_id   = site.id
        site_type = site.type
        count     = index(site.router, router) + 1
      }
    ]
  ])

  switches = flatten([
    for site in var.sites : [
      for switch in site.switches : {
        serial    = switch
        site_name = site.name
        site_id   = site.id
        site_type = site.type
        count     = index(site.switches, switch) + 1
      }
    ]
  ])
}

resource "netbox_site" "site" {
  for_each  = { for site in var.sites : site.id => site }
  name      = "${each.value.name}"
  latitude  = "47.4095"
  longitude = "8.5876"
  status    = "active"
  timezone  = "Europe/Zurich"
  tenant_id = netbox_tenant.brkops2357.id
}

resource "null_resource" "sites" {
  for_each = { for site in var.sites : site.name => site }
  triggers = {
    value = each.key
  }
  provisioner "local-exec" {
    when    = create
    command = "echo ADDED_SITE=${each.key} >> site.env"
  }
}

resource "netbox_prefix" "infra_site_prefix" {
  for_each    = { for site in var.sites : site.id => site }
  prefix      = each.value.type == "Branch" ? "10.${var.infra_vrf}.${each.value.id}.0/24" : "192.168.${var.infra_vrf}.0/24"
  status      = "active"
  description = "INFRA ${each.value.type} network ${each.value.name}"
  tenant_id   = netbox_tenant.brkops2357.id
  vrf_id      = netbox_vrf.infra.id
  vlan_id     = netbox_vlan.infra.id
  site_id     = netbox_site.site[each.value.id].id
}

resource "netbox_device" "router" {
  for_each       = { for device in local.router : device.serial => device }
  name           = "${each.value.site_name}-r0${each.value.count}"
  device_type_id = netbox_device_type.type["C8000V"].id
  role_id        = netbox_device_role.role[each.value.site_type].id
  site_id        = netbox_site.site[each.value.site_id].id
  platform_id    = netbox_platform.cisco_iosxe.id
  tenant_id      = netbox_tenant.brkops2357.id
  serial         = each.value.serial
}

resource "netbox_device" "switches" {
  for_each       = { for device in local.switches : device.serial => device }
  name           = "${each.value.site_name}-sw0${each.value.count}"
  device_type_id = netbox_device_type.type["C9KV-UADP-8P"].id
  role_id        = netbox_device_role.role[each.value.site_type].id
  site_id        = netbox_site.site[each.value.site_id].id
  platform_id    = netbox_platform.cisco_iosxe.id
  tenant_id      = netbox_tenant.brkops2357.id
  serial         = each.value.serial
}

resource "netbox_device_interface" "router_sdwan_system_intf" {
  for_each  = { for device in local.router : device.serial => device }
  name      = "Sdwan-system-intf"
  device_id = netbox_device.router[each.value.serial].id
  type      = "virtual"
}

resource "netbox_ip_address" "router_sdwan_system_intf_ip" {
  for_each            = { for device in local.router : device.serial => device }
  ip_address          = "10.255.${each.value.site_id}.${each.value.count}/32"
  status              = "active"
  device_interface_id = netbox_device_interface.router_sdwan_system_intf[each.value.serial].id
  tenant_id           = netbox_tenant.brkops2357.id
}

resource "netbox_device_interface" "router_wan_intf" {
  for_each    = { for device in local.router : device.serial => device }
  name        = var.router_wan_interface
  device_id   = netbox_device.router[each.value.serial].id
  type        = "1000base-t"
  description = "WAN"
}

resource "netbox_ip_address" "router_wan_intf_ip" {
  for_each            = { for device in local.router : device.serial => device }
  ip_address          = each.value.site_type == "Branch" ? "192.168.99.2${each.value.site_id}/24" : "192.168.99.20${each.value.site_id}/24"
  status              = "active"
  device_interface_id = netbox_device_interface.router_wan_intf[each.value.serial].id
  tenant_id           = netbox_tenant.brkops2357.id
}

resource "netbox_device_interface" "router_lan_intf" {
  for_each    = { for device in local.router : device.serial => device }
  name        = var.router_lan_interface
  device_id   = netbox_device.router[each.value.serial].id
  type        = "1000base-t"
  description = each.value.site_type == "Branch" ? "LAN" : "INFRA"
}

resource "netbox_device_interface" "switch_uplink_intf" {
  for_each    = { for device in local.switches : device.serial => device }
  name        = var.switch_uplink_interface
  device_id   = netbox_device.switches[each.value.serial].id
  type        = "1000base-t"
  mode        = "tagged"
  description = "Uplink"
}

resource "netbox_device_interface" "router_infra_intf" {
  for_each                   = { for device in local.router : device.serial => device if device.site_type == "Branch" }
  name                       = "${var.router_lan_interface}.${var.infra_vrf}"
  device_id                  = netbox_device.router[each.value.serial].id
  parent_device_interface_id = netbox_device_interface.router_lan_intf[each.value.serial].id
  type                       = "virtual"
  description                = "INFRA"
}

resource "netbox_ip_address" "router_infra_intf_ip" {
  for_each            = { for device in local.router : device.serial => device }
  ip_address          = each.value.site_type == "Branch" ? "10.${var.infra_vrf}.${each.value.site_id}.${each.value.count}/24" : "192.168.99.5${each.value.count}/24"
  status              = "active"
  device_interface_id = each.value.site_type == "Branch" ? netbox_device_interface.router_infra_intf[each.value.serial].id : netbox_device_interface.router_lan_intf[each.value.serial].id
  tenant_id           = netbox_tenant.brkops2357.id
  vrf_id              = netbox_vrf.infra.id
}

resource "netbox_device_interface" "switch_infra_intf" {
  for_each    = { for device in local.switches : device.serial => device }
  name        = "Vlan${var.infra_vrf}"
  device_id   = netbox_device.switches[each.value.serial].id
  type        = "virtual"
  description = "INFRA"
}

resource "netbox_ip_address" "switch_infra_intf_ip" {
  for_each            = { for device in local.switches : device.serial => device }
  ip_address          = "10.${var.infra_vrf}.${each.value.site_id}.1${each.value.count}/24"
  status              = "active"
  device_interface_id = netbox_device_interface.switch_infra_intf[each.value.serial].id 
  tenant_id           = netbox_tenant.brkops2357.id
  vrf_id              = netbox_vrf.infra.id
}

resource "netbox_device_primary_ip" "router" {
  for_each      = { for device in local.router : device.serial => device }
  device_id     = netbox_device.router[each.value.serial].id
  ip_address_id = netbox_ip_address.router_infra_intf_ip[each.value.serial].id
}

resource "netbox_device_primary_ip" "switch" {
  for_each      = { for device in local.switches : device.serial => device }
  device_id     = netbox_device.switches[each.value.serial].id
  ip_address_id = netbox_ip_address.switch_infra_intf_ip[each.value.serial].id
}
