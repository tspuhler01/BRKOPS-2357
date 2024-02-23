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
  general_templates = {
    for role in var.device_roles : role => concat(
      tolist(data.sdwan_feature_device_template.sample_template.general_templates),
      [
        for vpn in var.vpns : {
          site_type     = role
          id            = sdwan_cisco_vpn_feature_template.vpn[vpn.id].id
          type          = sdwan_cisco_vpn_feature_template.vpn[vpn.id].template_type
          sub_templates = [{
            id   = sdwan_cisco_vpn_interface_feature_template.vpn[vpn.id].id
            type = sdwan_cisco_vpn_interface_feature_template.vpn[vpn.id].template_type
          }]
        } if contains(vpn.sites, role)
      ]
    )
  }

  vpns_by_site = { for site in var.device_roles : site => [
    for vpn in var.vpns : vpn.id if contains(vpn.sites, site)
  ]}
}

data "sdwan_feature_device_template" "sample_template" {
  id = var.sample_template
}

data "sdwan_cisco_vpn_feature_template" "sample_template" {
  name = var.sample_vpn_template
}

data "sdwan_cisco_vpn_interface_feature_template" "sample_template" {
  name = var.sample_vpn_interface_template
}

resource "sdwan_cisco_vpn_feature_template" "vpn" {
  for_each           = { for vpn in var.vpns : vpn.id => vpn }
  name               = "cedge_vpn${each.value.id}"
  description        = "cedge_vpn${each.value.id}"
  device_types       = data.sdwan_cisco_vpn_feature_template.sample_template.device_types
  vpn_id             = each.value.id
  vpn_name           = each.value.name
  dns_ipv4_servers   = data.sdwan_cisco_vpn_feature_template.sample_template.dns_ipv4_servers
  ipv4_static_routes = data.sdwan_cisco_vpn_feature_template.sample_template.ipv4_static_routes
}

resource "sdwan_cisco_vpn_interface_feature_template" "vpn" {
  for_each                = { for vpn in var.vpns : vpn.id => vpn }
  name                    = "cedge_vpn${each.value.id}-eth"
  description             = "cedge_vpn${each.value.id}-eth"
  device_types            = data.sdwan_cisco_vpn_feature_template.sample_template.device_types
  shutdown                = false
  interface_name_variable = "vpn${each.value.id}_interface"
  address_variable        = "vpn${each.value.id}_ipv4_address"
  ipv4_dhcp_helper        = data.sdwan_cisco_vpn_interface_feature_template.sample_template.ipv4_dhcp_helper
}

resource "null_resource" "vpn" {
  for_each   = toset(var.device_roles)
  depends_on = [ sdwan_cisco_vpn_feature_template.vpn, sdwan_cisco_vpn_interface_feature_template.vpn ]
  triggers = {
    value = join(",", local.vpns_by_site[each.value])
  }
  provisioner "local-exec" {
    command = "python3 ../../../utils/sdwan.py template detach template ${each.value}"
  }
}

resource "sdwan_feature_device_template" "sites" {
  depends_on        = [ null_resource.vpn ]
  for_each          = toset(var.device_roles)
  name              = each.value
  description       = each.value
  device_type       = data.sdwan_feature_device_template.sample_template.device_type
  general_templates = local.general_templates[each.value]
  lifecycle {
    create_before_destroy = true
  }
}
