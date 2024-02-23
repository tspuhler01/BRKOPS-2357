"""
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
"""

import pynetbox
import requests
import ipaddress
import re
import copy

requests.packages.urllib3.disable_warnings()


class NetboxData:
    """
    This class abstracts the intent to get variables from netbox
    for routing and switching in the context of BRKOPS-2357. Interaction with netbox is done via pynetbox SDK.
    """

    def __init__(self, host=str, token=str, tenant=str) -> None:
        """
        initialising and creating netbox session

        :param host: netbox host.
        :param token: netbox token.
        :param tenant: netbox tenant.
        """
        self.host = host
        self.token = token
        self.tenant = tenant
        self.__session()

    def __session(self) -> None:
        self.nb = pynetbox.api(self.host, token=self.token)
        self.nb.http_session.verify = False

    def __get_device_roles_per_type(self, devices=dict):
        """
        Getting device role based on devices

        :param devices: devices to query.
        :return: Device roles.
        """
        all_device_roles = self.nb.dcim.device_roles.all()
        existing_roles = set(device["type"] for device in devices)
        device_roles = [
            role.name for role in all_device_roles if role.name in existing_roles
        ]

        return device_roles

    def __get_router_vars(self):
        """
        Retrieves the base variables for the routers

        :return: router_vars (base).
        """
        router_vars = []
        for site in self.site_data:
            for router in site["router"]:
                nb_router = self.nb.dcim.devices.get(serial=router)
                system_interface = self.nb.dcim.interfaces.get(
                    name="Sdwan-system-intf", device_id=nb_router.id
                )
                system_address = ipaddress.ip_interface(
                    self.nb.ipam.ip_addresses.get(interface_id=system_interface.id)
                )
                vpn0_interface = self.nb.dcim.interfaces.get(
                    description="WAN", device_id=nb_router.id
                )
                vpn0_interface_ip = self.nb.ipam.ip_addresses.get(
                    interface_id=vpn0_interface.id
                )
                vpn99_interface = self.nb.dcim.interfaces.get(
                    description="INFRA", device=nb_router.name
                )
                vpn99_interface_ip = self.nb.ipam.ip_addresses.get(
                    interface_id=vpn99_interface.id
                )
                router_vars.append(
                    {
                        "id": str(nb_router.serial),
                        "type": str(nb_router.role),
                        "variables": {
                            "system_site_id": site["id"],
                            "system_system_ip": str(system_address.ip),
                            "system_host_name": str(nb_router.name),
                            "vpn0_interface": str(vpn0_interface.name),
                            "vpn0_ipv4_address": str(vpn0_interface_ip.address),
                            "vpn99_interface": str(vpn99_interface.name),
                            "vpn99_ipv4_address": str(vpn99_interface_ip.address),
                        },
                    }
                )

        return router_vars

    def __get_router_vpns(self, router_vars):
        """
        Retrieves the vpn variables for the routers based on the base vars

        :param router_vars: base vars
        :return: appended router_vars and vpn variables.
        """
        for router in router_vars:
            for vpn in self.vpn_data:
                interface = self.nb.dcim.interfaces.get(
                    description=vpn["name"],
                    device=router["variables"]["system_host_name"],
                )
                ip_address = self.nb.ipam.ip_addresses.get(interface_id=interface.id)
                router["variables"][f"vpn{vpn['id']}_interface"] = str(interface)
                router["variables"][f"vpn{vpn['id']}_ipv4_address"] = str(ip_address)

        return router_vars, self.vpn_data

    def __get_switch_vars(self):
        """
        Retrieves the switch variables

        :return: switch_vars.
        """
        switch_vars = []
        for site in self.site_data:
            for switch in site["switches"]:
                nb_switch = self.nb.dcim.devices.get(serial=switch)
                switch_vars.append(
                    {
                        "id": str(nb_switch.serial),
                        "name": str(nb_switch.name),
                        "site": str(nb_switch.site),
                        "type": str(nb_switch.role),
                    }
                )

        return switch_vars

    def __get_switch_vlans(self, switch_vars=dict):
        """
        Retrieves the vlan variables for the switches based on the switch vars

        :param switch_vars: switch_vars
        :return: vlan_data variables.
        """
        vlan_data = copy.deepcopy(self.vpn_data)
        for vpn in vlan_data:
            interface_dict = {}
            sites = set()
            for switch in switch_vars:
                nb_interfaces = self.nb.dcim.interfaces.filter(
                    description=vpn["name"], device=switch["name"]
                )
                sites.add(switch["type"])
                for interface in nb_interfaces:
                    parsed_interface = self.__parse_interface(str(interface))
                    if parsed_interface:
                        interface_key = (
                            f"{parsed_interface['type']}:{parsed_interface['name']}"
                        )
                        interface_dict[interface_key] = parsed_interface

            vpn["sites"] = list(sites)
            vpn["interfaces"] = list(interface_dict.values())

        return vlan_data

    def __parse_interface(self, interface=str):
        match = re.match(
            r"(GigabitEthernet|TenGigabitEthernet)(\d+/\d+/\d+)", interface
        )
        if match:
            return {"type": match.group(1), "name": match.group(2)}
        return None

    def service_data(self, site_data=dict, vpn_data=dict):
        self.site_data = site_data["site-service:sites"]
        self.vpn_data = vpn_data["vpn-service:vpns"]

    def build_routing_vars(self):
        """
        Builds the final routing_vars used for deploying with terraform

        :return: routing_vars (terraform.tfvars.json).
        """
        router_base_vars = self.__get_router_vars()
        router_vars, router_vpns = self.__get_router_vpns(router_base_vars)
        router_roles = self.__get_device_roles_per_type(devices=router_vars)

        routing_vars = {
            "router": router_vars,
            "vpns": router_vpns,
            "device_roles": router_roles,
        }

        return routing_vars

    def build_switching_vars(self):
        """
        Builds the final switching_vars used for deploying with terraform

        :return: switching_vars (terraform.tfvars.json).
        """
        site_vars = self.__get_switch_vars()
        vlans = self.__get_switch_vlans(switch_vars=site_vars)
        roles = self.__get_device_roles_per_type(devices=site_vars)

        switching_vars = {"switches": site_vars, "vlans": vlans, "device_roles": roles}

        return switching_vars
