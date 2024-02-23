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
  routers_by_type = {
    for role in var.device_roles : role => [
      for router in var.router : router if router.type == role
    ]
  }
}

resource "sdwan_attach_feature_device_template" "attach_sites" {
  for_each = local.routers_by_type
  id       = sdwan_feature_device_template.sites[each.key].id
  devices  = [
    for router in each.value : {
      id = router.id
      variables = router.variables
    }
  ]
}

resource "null_resource" "cleanup" {
  for_each = { for router in var.router : router.id => router }
  triggers = {
    value = each.key
  }
  provisioner "local-exec" {
    when    = destroy
    command = "python3 ../../../utils/sdwan.py template detach device ${each.key}"
  }
}
