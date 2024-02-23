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

from vmanage.api.authentication import Authentication
from vmanage.api.device_templates import DeviceTemplates
from vmanage.api.http_methods import HttpMethods
from vmanage.api.utilities import Utilities
from vmanage.api.device import Device
import click
import json
import os


class Sdwan:
    """
    This class encapsulates operations for managing SD-WAN devices and templates via vManage.
    It supports operations like getting device details, listing devices by template, and detaching devices from templates.
    """

    def __init__(self) -> None:
        self.host = os.getenv("VMANAGE_HOST")
        self.user = os.getenv("VMANAGE_USER")
        self.password = os.getenv("VMANAGE_PASSWORD")
        self.session = Authentication(
            host=self.host, user=self.user, password=self.password
        ).login()

    def get_device(self, device_uuid=str):
        """
        Retrieves details for a specific device using its UUID.

        :param device_uuid: Unique identifier of the device.
        :return: Device details.
        """

        devices = Device(session=self.session, host=self.host)
        device = devices.get_device_status(value=device_uuid, key="uuid")
        return device

    def get_devices_by_template(self, template_name=str):
        """
        Lists devices associated with a specific template name.

        :param template_name: Name of the device template.
        :return: List of devices using the specified template.
        """

        device_templates = DeviceTemplates(session=self.session, host=self.host)
        template = device_templates.get_device_template_dict(
            key_name="templateName", name_list=template_name
        )
        if template:
            template_id = template[template_name]["templateId"]
            devices = device_templates.get_template_attachments(
                template_id=template_id, key="uuid"
            )
            return devices

    def wait_for_completion(self, id=str):
        """
        Waits for a task (e.g., device detachment) to complete based on its ID.

        :param id: The action ID to wait for.
        :return: Completion status.
        """

        utils = Utilities(session=self.session, host=self.host)
        return utils.waitfor_action_completion(action_id=id)

    def detach_devices(self, devices=list, device_type="vedge"):
        """
        Detaches a list of devices from their template.

        :param devices: List of device UUIDs to detach.
        :param device_type: Type of the devices, default is 'vedge'.
        :return: Detachment status or error.
        """

        devices_payload = []
        for device in devices:
            devices_payload.append({"deviceId": device})

        url = HttpMethods(
            session=self.session,
            url=f"https://{self.host}/dataservice/template/config/device/mode/cli",
        )
        payload = json.dumps({"deviceType": device_type, "devices": devices_payload})
        response = url.request(method="POST", payload=payload)

        if response["status_code"] != 200:
            return response["error"]

        task_id = response["json"]["id"]
        return self.wait_for_completion(id=task_id)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(Sdwan)


@cli.group()
def template():
    pass


@template.group()
def detach():
    pass


@detach.command(name="template")
@click.argument("template_name")
@click.pass_obj
def detach_all_device_from_template(obj, template_name):
    devices = obj.get_devices_by_template(template_name)
    if devices:
        obj.detach_devices(devices)


@detach.command(name="device")
@click.argument("device_uuid")
@click.pass_obj
def detach_device(obj, device_uuid):
    device = obj.get_device(device_uuid)
    if device:
        devices = []
        devices.append(device_uuid)
        obj.detach_devices(devices)
    else:
        print("device not found")


if __name__ == "__main__":
    cli()
