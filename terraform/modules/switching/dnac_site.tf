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
  all_sites = [for sw in var.switches : sw.site]
  sites     = distinct(local.all_sites)
}

resource "dnacenter_area" "area" {
  parameters {
    site {
      area {
        name        = var.tenant
        parent_name = "Global"
      }
    }
    type    = "area"
  }
}

resource "dnacenter_area" "site" {
  depends_on = [ dnacenter_area.area ]
  for_each   = toset(local.sites)
  parameters {
    site {
      area {
        name        = each.value
        parent_name = "Global/${var.tenant}"
      }
    }
    type = "area"
  }
}

resource "dnacenter_building" "site_building" {
  depends_on = [ dnacenter_area.site ]
  for_each   = toset(local.sites)
  parameters {
    site {
      building {
        address     = "Richtistrasse 7, 8304 Wallisellen, Switzerland"
        latitude    = 47.409871
        longitude   = 8.590509
        name        = "Building"
        parent_name = "Global/${var.tenant}/${each.value}"
      }
    }
    type = "building"
  }
}
