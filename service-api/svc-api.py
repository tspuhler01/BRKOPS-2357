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

from flask import Flask
from flask_restx import Resource, Api, reqparse
import requests
import json
import gitlab
import datetime
import base64
import os

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Services API",
    description="Service API for managing EN Infrastructure in BRKOPS-2357",
)

sites = api.namespace("site", description="site management")

vpns = api.namespace("vpn", description="vpn management")

infra = api.namespace("infra", description="infrastructure")


class ServiceDb:
    """
    This class is responsible to interact with the service database through RESTCONF for managing VPNs and sites.
    """

    def __init__(self) -> None:
        service_db_url = os.getenv("SERVICE_DB_URL")
        self.url = f"{service_db_url}/restconf/data"

    def get_vpn_all(self):
        response = requests.get(f"{self.url}/vpn-service:vpns")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.json()

    def get_vpn_by_id(self, id=str):
        response = requests.get(f"{self.url}/vpn-service:vpns={id}")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.json()

    def post_vpn(self, id=int, name=str, sites=list):
        payload = {"vpns": [{"id": id, "name": name, "sites": sites}]}
        response = requests.post(
            f"{self.url}/vpn-service:vpns", data=json.dumps(payload)
        )
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code

    def patch_vpn(self, id=int, name=str, sites=list):
        payload = {"name": name, "sites": sites}
        response = requests.patch(
            f"{self.url}/vpn-service:vpns={id}", data=json.dumps(payload)
        )
        print(response)
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code

    def delete_vpn(self, id=int):
        response = requests.delete(f"{self.url}/vpn-service:vpns={id}")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code

    def get_site_all(self):
        response = requests.get(f"{self.url}/site-service:sites")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.json()

    def get_site_by_id(self, id):
        response = requests.get(f"{self.url}/site-service:sites={id}")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.json()

    def post_site(self, id=int, name=str, type=str, router=list, switches=list):
        payload = {
            "sites": [
                {
                    "id": id,
                    "name": name,
                    "type": type,
                    "router": router,
                    "switches": switches,
                }
            ]
        }
        response = requests.post(
            f"{self.url}/site-service:sites", data=json.dumps(payload)
        )
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code

    def patch_site(self, id=int, name=str, type=str, router=list, switches=list):
        payload = {"name": name, "type": type, "router": router, "switches": switches}
        response = requests.patch(
            f"{self.url}/site-service:sites={id}", data=json.dumps(payload)
        )
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code

    def delete_site(self, id=int):
        response = requests.delete(f"{self.url}/site-service:sites={id}")
        if response.status_code != 200:
            return {"error": response.content.decode("utf-8")}
        return response.status_code


class Git:
    """
    A class to interact with GitLab for version control operations.
    """

    def __init__(self):
        self.private_token = os.getenv("GITLAB_TOKEN")
        self.url = os.getenv("GITLAB_URL")
        self.project_id = os.getenv("GITLAB_PROJECT_ID")
        self.gl = gitlab.Gitlab(self.url, private_token=self.private_token)
        self.project = self.gl.projects.get(self.project_id)

    def __create_branch(self):
        now = datetime.datetime.now()
        date = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}"

        branch_name = f"services_{date}"
        self.new_branch = self.project.branches.create(
            {"branch": branch_name, "ref": "main"}
        )

    def __commit_to_branch(self, site_service_data, vpn_service_data):

        site_service_file_path = os.getenv("SITE_SERVICE")
        vpn_service_file_path = os.getenv("VPN_SERVICE")

        site_service_file = self.project.files.get(
            file_path=site_service_file_path, ref=self.new_branch.name
        )
        vpn_service_file = self.project.files.get(
            file_path=vpn_service_file_path, ref=self.new_branch.name
        )
        site_service_file_content = base64.b64decode(site_service_file.content).decode(
            "utf-8"
        )
        vpn_service_file_content = base64.b64decode(vpn_service_file.content).decode(
            "utf-8"
        )

        if site_service_file_content != site_service_data:
            site_service_file.content = site_service_data
            site_service_file.save(
                branch=self.new_branch.name,
                commit_message="site service update by service-api",
                author_email="service-api@its-best.ch",
                author_name="service-api",
            )

        if vpn_service_file_content != vpn_service_data:
            vpn_service_file.content = vpn_service_data
            vpn_service_file.save(
                branch=self.new_branch.name,
                commit_message="vpn service update by service-api",
                author_email="service-api@its-best.ch",
                author_name="service-api",
            )

    def __create_merge_request(self):

        self.merge_request = self.project.mergerequests.create(
            {
                "source_branch": self.new_branch.name,
                "target_branch": "main",
                "title": self.new_branch.name,
                "remove_source_branch": True,
            }
        )

        return self.merge_request.state

    def push_to_infra(self):
        """
        Pushes the site and VPN service data to the infrastructure repository in GitLab.

        :return: The state of the created merge request.
        """
        site_service = services.get_site_all()
        site_service["site-service:sites"] = site_service.pop("sites")
        site_service_json = json.dumps(site_service, indent=4)
        vpn_service = services.get_vpn_all()
        vpn_service["vpn-service:vpns"] = vpn_service.pop("vpns")
        vpn_service_json = json.dumps(vpn_service, indent=4)

        self.__create_branch()
        self.__commit_to_branch(
            site_service_data=site_service_json, vpn_service_data=vpn_service_json
        )
        return {"merge_request_state": self.__create_merge_request()}


services = ServiceDb()
git = Git()

vpn_post_parser = reqparse.RequestParser()
vpn_post_parser.add_argument("id", type=int, required=True, help="VPN ID")
vpn_post_parser.add_argument("name", type=str, required=True, help="VPN Name")
vpn_post_parser.add_argument(
    "sites",
    type=str,
    required=True,
    choices=("DC", "Branch"),
    action="append",
    help="DC and/or Branch",
)

vpn_patch_parser = reqparse.RequestParser()
vpn_patch_parser.add_argument("name", type=str, required=False, help="VPN Name")
vpn_patch_parser.add_argument(
    "sites",
    type=str,
    required=False,
    choices=("DC", "Branch"),
    action="append",
    help="DC and/or Branch",
)

site_post_parser = reqparse.RequestParser()
site_post_parser.add_argument("id", type=int, required=True, help="Site ID")
site_post_parser.add_argument("name", type=str, required=True, help="Site Name")
site_post_parser.add_argument(
    "type", type=str, required=True, choices=("DC", "Branch"), help="DC or Branch"
)
site_post_parser.add_argument(
    "router", type=str, required=True, action="append", help="Router serial numbers"
)
site_post_parser.add_argument(
    "switches", type=str, required=True, action="append", help="Switch serial numbers"
)

site_patch_parser = reqparse.RequestParser()
site_patch_parser.add_argument("name", type=str, required=False, help="Site Name")
site_patch_parser.add_argument(
    "type", type=str, required=False, choices=("DC", "Branch"), help="DC or Branch"
)
site_patch_parser.add_argument(
    "router", type=str, required=False, action="append", help="Router serial numbers"
)
site_patch_parser.add_argument(
    "switches", type=str, required=False, action="append", help="Switch serial numbers"
)


@vpns.route("/")
class AllVpns(Resource):

    def get(self):
        return services.get_vpn_all()

    @api.expect(vpn_post_parser)
    def post(self):
        args = vpn_post_parser.parse_args()
        return services.post_vpn(id=args.id, name=args.name, sites=args.sites)


@vpns.route("/<int:id>")
class VpnId(Resource):

    def get(self, id):
        return services.get_vpn_by_id(id)

    @api.expect(vpn_patch_parser)
    def patch(self, id):
        args = vpn_patch_parser.parse_args()
        return services.patch_vpn(id=id, name=args.name, sites=args.sites)

    def delete(self, id):
        return services.delete_vpn(id)


@sites.route("/")
class AllSites(Resource):

    def get(self):
        return services.get_site_all()

    @api.expect(site_post_parser)
    def post(self):
        args = site_post_parser.parse_args()
        return services.post_site(
            id=args.id,
            name=args.name,
            type=args.type,
            router=args.router,
            switches=args.switches,
        )


@sites.route("/<int:id>")
class SiteId(Resource):

    def get(self, id):
        return services.get_site_by_id(id)

    @api.expect(site_patch_parser)
    def patch(self, id):
        args = site_patch_parser.parse_args()
        return services.patch_site(
            id=id,
            name=args.name,
            type=args.type,
            router=args.router,
            switches=args.switches,
        )

    def delete(self, id):
        return services.delete_site(id)


@infra.route("/commit")
class Commit(Resource):

    def post(self):
        return git.push_to_infra()


if __name__ == "__main__":
    app.run(debug=True)
