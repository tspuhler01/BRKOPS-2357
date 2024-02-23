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

provider "netbox" {
  server_url           = var.netbox_url
  api_token            = var.netbox_token
  allow_insecure_https = true
}

module "netbox" {
  source                  = "../../../terraform/modules/netbox"
  tenant                  = var.tenant
  rir                     = var.rir
  aggregates              = var.aggregates
  underlay_prefix         = var.underlay_prefix
  sdwan_system_ip_prefix  = var.sdwan_system_ip_prefix
  device_manufacturer     = var.device_manufacturer
  device_type             = var.device_type
  device_roles            = var.device_roles
  infra_vrf               = var.infra_vrf
  infra_prefix            = var.infra_prefix
  router_wan_interface    = var.router_wan_interface
  router_lan_interface    = var.router_lan_interface
  switch_uplink_interface = var.switch_uplink_interface
  vpns                    = var.vpns
  sites                   = var.sites
}
