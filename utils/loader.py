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

from yangson import DataModel
from netbox import NetboxData
import json
import logging
import sys
import click
import os


class DataLoader:
    """
    This class is responsible for loading data from NetBox based on predefined service definitions (like Sites and VPNs)
    and validates this data against YANG models. If the data is validated successfully, it writes the data to terraform.tfvars.json
    files for both routing and switching configurations. The class uses the NetboxData to fetch data according to the service definition.
    """

    def __init__(self) -> None:
        """
        Initializes the DataLoader instance with NetBox connection details and sets up logging.
        """

        self.host = os.getenv("NETBOX_URL")
        self.token = os.getenv("NETBOX_TOKEN")
        self.tenant = os.getenv("TENANT")
        self.__session()
        logging.basicConfig(level=logging.INFO)

    def __session(self):
        self.netbox = NetboxData(host=self.host, token=self.token, tenant=self.tenant)

    def __rename_keys(self, data, prefix):
        """
        Renames keys in a dictionary by adding a prefix.

        :param data: The original dictionary whose keys are to be renamed.
        :param prefix: The prefix to add to each key in the dictionary.
        :return: A new dictionary with keys renamed.
        """

        return {prefix + key: value for key, value in data.items()}

    def __validate_data(self, library, data):
        """
        Validates the provided data against the YANG model specified in the library.

        :param library: The file path to the YANG model library.
        :param data: The data to be validated.
        """

        module_paths = ["../yang/modules"]
        dm = DataModel.from_file(library, module_paths)
        data = dm.from_raw(data)

        try:
            data.validate()
            logging.info(msg="Data validation: success")

        except Exception as e:
            logging.error(msg=f"Data validation: failed. {e}")
            sys.exit(1)

    def load_service_data(self):
        """
        Loads service data from predefined JSON files and validates it against YANG models.

        :return: The loaded and validated service data as a dictionary.
        """

        site_service_file = "../services/sites.json"
        vpn_service_file = "../services/vpns.json"
        service_library = "../yang/library/yang-library-services.json"
        service_data = {}

        with open(site_service_file) as file:
            self.site_service = json.load(file)
            service_data.update(self.site_service)

        with open(vpn_service_file) as file:
            self.vpn_service = json.load(file)
            service_data.update(self.vpn_service)

        logging.info(msg="Service data loading: success")

        self.__validate_data(service_library, service_data)

        return service_data

    def load_vars(self, service_data):
        """
        Generates routing and switching variables from the service data, renames the keys, and validates the variables.

        :param service_data: The previously loaded and validated service data.
        :return: A tuple containing dictionaries for routing and switching variables.
        """

        vars_library = "../yang/library/yang-library-variables.json"
        self.netbox.service_data(site_data=self.site_service, vpn_data=self.vpn_service)

        routing_vars = self.netbox.build_routing_vars()
        service_data.update(self.__rename_keys(routing_vars, "routing:"))
        switching_vars = self.netbox.build_switching_vars()
        service_data.update(self.__rename_keys(switching_vars, "switching:"))

        logging.info(msg="Loading variables: success")
        self.__validate_data(vars_library, service_data)
        return routing_vars, switching_vars

    def save_vars(self, service=False, routing=False, switching=False) -> None:
        """
        Writes the service, routing, and switching variables to separate terraform.tfvars.json files.

        :param service: Dictionary containing the service data to be saved.
        :param routing: Dictionary containing the routing variables to be saved.
        :param switching: Dictionary containing the switching variables to be saved.
        """

        if service:
            netbox = {
                (
                    "sites"
                    if k == "site-service:sites"
                    else "vpns" if k == "vpn-service:vpns" else k
                ): v
                for k, v in service.items()
            }
            with open(
                "../services/terraform/netbox/terraform.tfvars.json", "w"
            ) as file:
                file.write(json.dumps(netbox, indent=2))
        if routing:
            with open(
                "../services/terraform/routing/terraform.tfvars.json", "w"
            ) as file:
                file.write(json.dumps(routing, indent=2))
        if switching:
            with open(
                "../services/terraform/switching/terraform.tfvars.json", "w"
            ) as file:
                file.write(json.dumps(switching, indent=2))
        logging.info(msg="Saving variables: success")


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(DataLoader)


@cli.command()
@click.pass_obj
def services(obj):
    service_data = obj.load_service_data()
    obj.save_vars(service=service_data)


@cli.command()
@click.pass_obj
def variables(obj):
    service_data = obj.load_service_data()
    routing_vars, switching_vars = obj.load_vars(service_data)
    obj.save_vars(routing=routing_vars, switching=switching_vars)


if __name__ == "__main__":
    cli()
