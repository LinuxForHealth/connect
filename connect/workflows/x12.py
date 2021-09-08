from connect.workflows.core import CoreWorkflow
from fastapi import Response
from datetime import datetime
from connect.support.timer import timer
import logging
from typing import Dict, Optional
import xworkflows
from httpx import AsyncClient
from x12.io import X12ModelReader


logger = logging.getLogger(__name__)


class X12Workflow(CoreWorkflow):
    """
    Custom workflow used to persist a X12 message and convert it to FHIR.
    """

    def parse_x12_last_org_name(self, target_loop: str, x12_record: Dict) -> str:
        """Parses the last/org name from a X12 loop"""
        return x12_record[target_loop]["nm1_segment"]["name_last_or_organization_name"]

    def parse_x12_first_name(self, target_loop: str, x12_record: Dict) -> str:
        """Parses the first name from a X12 loop"""
        return x12_record[target_loop]["nm1_segment"]["name_first"]

    async def find_resource_id(
        self, client, fhir_url, resource, search: Dict
    ) -> Optional[str]:
        """
        Finds a FHIR resource id given search parameters.

        :param client: The httpx async client
        :param fhir_url: Base URL for the FHIR server
        :param resource: The resource name/domain to search
        :param search: dictionary of search parameters
        """
        r = await client.get(f"{fhir_url}/{resource}", params=search)
        search_result = r.json()
        total_hits = search_result.get("total", 0)

        if total_hits > 0:
            entry = search_result.get("entry", [{}])[0]
            resource_id = entry.get("resource", {}).get("id")
            return resource_id
        else:
            return None

    @xworkflows.transition("do_transform")
    @timer
    async def transform(self):
        """
        Transforms a X12 270 eligibility message to FHIR R4 CoverageEligibilityRequest.
        The updated data record is stored within the transformed_data attribute.

        """
        self.transformed_data = {
            "resourceType": "CoverageEligibilityRequest",
            "text": {
                "status": "generated",
                "div": '<div xmlns="http://www.w3.org/1999/xhtml">A human-readable rendering of the CoverageEligibilityRequest</div>',
            },
            "status": "active",
            "priority": {"coding": [{"code": "normal"}]},
            "purpose": ["validation"],
            "patient": {
                "reference": "Patient/17bc6292c24-c8785d7f-32b0-4ebd-ba57-b7005c83c093"
            },
            "created": "2021-07-06",
            "provider": {
                "reference": "Organization/17bc6292aae-d5387fd6-86c1-409b-bc53-f8ed0779c120"
            },
            "insurer": {
                "reference": "Organization/17bc62928df-132d2ee6-9a93-44bd-acf9-46a01828c25c"
            },
            "insurance": [
                {
                    "focal": True,
                    "coverage": {
                        "reference": "Coverage/17bc6292ded-7935230c-4bf9-4821-b032-4afc7a1692b4"
                    },
                }
            ],
        }

        with X12ModelReader(self.message) as r:
            x12_model = list(r.models())[0]

        async with AsyncClient(verify=self.verify_certs) as c:
            fhir_url = self.transmit_servers[0]

            payor_name = self.parse_x12_last_org_name(
                "loop_2100a", x12_model.information_source
            )
            payor_id = await self.find_resource_id(
                c, fhir_url, "Organization", {"name": payor_name}
            )
            self.transformed_data["insurer"]["reference"] = f"Organization/{payor_id}"

            provider_name = self.parse_x12_last_org_name(
                "loop_2100b", x12_model.information_receiver
            )
            provider_id = await self.find_resource_id(
                c, fhir_url, "Organization", {"name": provider_name}
            )
            self.transformed_data["provider"][
                "reference"
            ] = f"Organization/{provider_id}"

            patient_last_name = self.parse_x12_last_org_name(
                "loop_2100c", x12_model.subscriber
            )
            patient_first_name = self.parse_x12_first_name(
                "loop_2100c", x12_model.subscriber
            )
            patient_id = await self.find_resource_id(
                c,
                fhir_url,
                "Patient",
                {"name": [patient_last_name, patient_first_name]},
            )
            self.transformed_data["patient"]["reference"] = f"Patient/{patient_id}"

            coverage_id = await self.find_resource_id(
                c, fhir_url, "Coverage", {"identifier": "12345"}
            )
            self.transformed_data["insurance"][0]["coverage"][
                "reference"
            ] = f"Coverage/{coverage_id}"

    @timer
    async def run(self, response: Response):
        """
        Run the workflow according to the defined states.  Override to extend or exclude states
        for a particular implementation.

        :return: the response instance, with updated body and status_code
        """
        self.start_time = datetime.utcnow()

        try:
            # trace log
            logger.trace(f"Running {self.__class__.__name__}")
            await self.validate()
            await self.transform()
            await self.persist()
            await self.synchronize()
            # await handle_fhir_resource(Request(), Response(), get_settings())
            return self.message
        except Exception as ex:
            msg = await self.error(ex)
            raise Exception(msg)
