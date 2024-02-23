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

resource "netbox_tenant" "brkops2357" {
  name        = var.tenant
  description = "Tenant ${var.tenant}"
}

resource "netbox_rir" "rfc1918" {
  name        = var.rir
  description = var.rir
}

resource "netbox_aggregate" "rfc1918" {
  for_each    = toset(var.aggregates)
  prefix      = each.value
  description = var.rir
  rir_id      = netbox_rir.rfc1918.id
  tenant_id   = netbox_tenant.brkops2357.id
}

resource "netbox_prefix" "underlay_prefix" {
  prefix      =  var.underlay_prefix
  status      = "active"
  description = "underlay"
  tenant_id   = netbox_tenant.brkops2357.id
}

resource "netbox_prefix" "sdwan_system-ip" {
  prefix      = var.sdwan_system_ip_prefix
  status      = "active"
  description = "SD-WAN System IPs"
  tenant_id   = netbox_tenant.brkops2357.id
}

resource "netbox_manufacturer" "cisco" {
  name = var.device_manufacturer
}

resource "netbox_platform" "cisco_iosxe" {
  name = "iosxe"
}

resource "netbox_device_type" "type" {
  for_each        = toset(var.device_type)
  model           = each.value
  manufacturer_id = netbox_manufacturer.cisco.id
}

resource "netbox_device_role" "role" {
  for_each  = toset(var.device_roles)
  name      = each.value
  color_hex = each.value == "Branch" ? "2986cc" : "8fce00"
}

resource "netbox_vrf" "infra" {
  name        = var.infra_vrf
  description = "INFRA"
  tenant_id   = netbox_tenant.brkops2357.id
}

resource "netbox_vlan" "infra" {
  name      = "INFRA"
  vid       = var.infra_vrf
  tenant_id = netbox_tenant.brkops2357.id
}

resource "netbox_prefix" "infra_prefix" {
  prefix      = var.infra_prefix
  status      = "active"
  description = "INFRA networks"
  tenant_id   = netbox_tenant.brkops2357.id
  vrf_id      = netbox_vrf.infra.id
}
