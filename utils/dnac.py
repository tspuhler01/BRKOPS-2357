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

from dnacentersdk import api
import logging
import click
import time
import os


class Dnac:
    """
    This class manages interactions with Cisco Catalyst Center using the dnacentersdk.
    It enables operations such as retrieving device onboarding state, getting device details,
    and deleting devices.
    """

    def __init__(self) -> None:
        self.host = os.getenv("DNAC_URL")
        self.user = os.getenv("DNAC_USER")
        self.password = os.getenv("DNAC_PASSWORD")
        self.session = api.DNACenterAPI(
            base_url=self.host, username=self.user, password=self.password, verify=False
        )
        logging.basicConfig(level=logging.INFO)

    def get_onboarding_state(self, device=str, wait=False):
        """
        Retrieves the onboarding state of a device. Optionally waits for the device to be provisioned.

        :param device: Serial number of the device.
        :param wait: If True, continuously checks until the device is provisioned.
        :return: The state of the device.
        """

        if wait:
            while True:
                response = self.session.device_onboarding_pnp.get_device_list(
                    serial_number=device
                )
                state = response[0]["deviceInfo"]["state"]

                if state == "Provisioned":
                    logging.info(msg=f"Onboarding state: {state}")
                    return state

                time.sleep(5)
        else:
            response = self.session.device_onboarding_pnp.get_device_list(
                serial_number=device
            )
            state = response[0]["deviceInfo"]["state"]

        logging.info(msg=f"Onboarding state: {state}")
        return state

    def get_device(self, device):
        """
        Retrieves a device ID based on its serial number.

        :param device: Serial number of the device.
        :return: Device ID if found, False otherwise.
        """

        response = self.session.devices.get_device_list(serial_number=device)
        try:
            device_id = response["response"][0]["id"]
            return device_id
        except Exception as e:
            logging.error(msg="Device not found")
            return False

    def delete_device(self, device_id=str):
        """
        Deletes a device from Catalyst Center.

        :param device_id: ID of the device to be deleted.
        :return: State of the operation.
        """

        response = self.session.devices.delete_device_by_id(
            id=device_id, is_force_delete=True
        )
        task_id = response["response"]["taskId"]

        while True:
            response = self.session.task.get_task_by_id(task_id=task_id)
            state = response["response"]["progress"]
            if state == "Network device deleted successfully":
                logging.info(msg=f"Delete state: {state}")
                return state
            time.sleep(5)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(Dnac)


@cli.group()
def device():
    pass


@device.group()
def get():
    pass


@device.command(name="delete")
@click.argument("device_serial")
@click.pass_obj
def delete_device(obj, device_serial):
    device_id = obj.get_device(device_serial)
    if device_id:
        return obj.delete_device(device_id)


@get.command(name="onboarding-state")
@click.argument("device_serial")
@click.option("--wait", is_flag=True, help="Wait for device to be provisioned")
@click.pass_obj
def get_onboarding_state(obj, device_serial, wait):
    return obj.get_onboarding_state(device=device_serial, wait=wait)


if __name__ == "__main__":
    cli()
