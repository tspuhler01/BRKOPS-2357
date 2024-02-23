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

variable "vmanage_url" {
    type = string
}

variable "vmanage_username" {
    type = string
}

variable "vmanage_password" {
    type = string
}

variable "sample_template" {
    type = string
}

variable "sample_vpn_template" {
    type = string
}

variable "sample_vpn_interface_template" {
    type = string
}

variable device_roles {
    type = list(string)
}

variable vpns {
    type = list(object({
        id    = string
        name  = string
        sites = list(string)
    }))
}

variable router {
    type = list(object({
        id        = string
        type      = string
        variables = map(string)
    }))
}

