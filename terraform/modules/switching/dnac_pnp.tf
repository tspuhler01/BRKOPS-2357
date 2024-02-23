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

data "dnacenter_configuration_template_project" "onboarding" {
  name = "Onboarding Configuration"
}

resource "dnacenter_configuration_template" "onboarding" {
  for_each = toset(var.device_roles)
  parameters {
    name             = "${var.tenant}_${each.value}_Onboarding"
    project_id       = data.dnacenter_configuration_template_project.onboarding.items.0.id
    software_type    = "IOS-XE"
    software_variant = "XE"
    language         = "JINJA"
    device_types {
      product_family = "Switches and Hubs"
      product_series = "Cisco Catalyst 9000 Series Virtual Switches"
      product_type   = "Cisco Catalyst 9000 UADP 8 Port Virtual Switch"
    }
    template_content =  <<-EOT
        hostname {{ hostname }}
        !
        ip routing
        !
        vlan ${var.infra_vrf}
         name INFRA
        !
        interface vlan ${var.infra_vrf}
         description INFRA
         no shutdown
         ip address dhcp
         no ip redirects
         no ip proxy-arp
        ! 
        interface ${var.switch_uplink_interface}
         description UPLINK to SDWAN
         no shutdown
         switchport nonegotiate
         switchport mode trunk
         spanning-tree portfast trunk
         spanning-tree bpduguard enable
        !
        interface range GigabitEthernet1/0/2 - 8
         description UNUSED
         shutdown
         switchport mode access
         switchport access vlan 1
         spanning-tree portfast
         spanning-tree bpduguard enable
        !
        ip http secure-server
        !
        netconf-yang
        restconf
        !
  EOT     
  }
}

resource "dnacenter_configuration_template_version" "onboarding" {
  for_each   = toset(var.device_roles)
  depends_on = [ dnacenter_configuration_template.onboarding ]
  parameters {
    template_id = dnacenter_configuration_template.onboarding[each.key].item.0.id
  }
}

data "dnacenter_pnp_device" "switch" {
  for_each      = { for switch in var.switches : switch.id => switch }
  serial_number = [ each.value.id ]
}

resource "dnacenter_pnp_device_site_claim" "branch" {
  for_each = { for switch in var.switches : switch.id => switch if switch.type == "Branch" }  
  parameters {
    device_id = data.dnacenter_pnp_device.switch[each.value.id].items.0.id
    site_id   = dnacenter_building.site_building[each.value.site].item.0.id
    type      = "Default"
    config_info {
      config_id = dnacenter_configuration_template.onboarding[each.value.type].item.0.id
      config_parameters {
        key   = "hostname"
        value = each.value.name
      }
    }
  }
}

resource "null_resource" "onboarding_state" {
  depends_on = [ dnacenter_pnp_device_site_claim.branch ]
  for_each   = { for switch in var.switches : switch.id => switch }
  triggers   = {
    value = each.key
  }
  provisioner "local-exec" {
    when    = create
    command = "python3 ../../../utils/dnac.py device get onboarding-state --wait ${each.key}"
  }
}

resource "null_resource" "cleanup" {
  depends_on = [ dnacenter_pnp_device_site_claim.branch ]
  for_each   = { for switch in var.switches : switch.id => switch }
  triggers   = {
    value    = each.key
  }
  provisioner "local-exec" {
    when    = destroy
    command = "python3 ../../../utils/dnac.py device delete ${each.key}"
  }
}