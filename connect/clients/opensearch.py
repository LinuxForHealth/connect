"""
opensearch.py
OpenSearch client wrapper
"""
import json
import logging
from connect.config import get_settings
from opensearchpy import OpenSearch
from opensearchpy.exceptions import RequestError
from typing import Any, Optional


logger = logging.getLogger(__name__)
opensearch_client = None


async def get_opensearch_client() -> Optional[OpenSearch]:
    """
    Create or return an OpenSearch client connected to the local
    OpenSearch server.

    :return: a connected OpenSearch client instance
    """
    global opensearch_client

    if not opensearch_client:
        opensearch_client = await create_opensearch_client()

    return opensearch_client


async def create_opensearch_client() -> Optional[OpenSearch]:
    """
    Create an OpenSearch client, connected to the configured OpenSearch server.

    :return: a connected OpenSearch client instance
    """
    settings = get_settings()

    # Create the client with SSL/TLS enabled, but hostname verification disabled
    client = OpenSearch(
        hosts=[{"host": settings.opensearch_server, "port": settings.opensearch_port}],
        http_compress=True,  # enables gzip compression for request bodies
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=True,
        verify_certs=settings.certificate_verify,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        ca_certs=settings.certificate_authority_path,
    )

    logger.info("Created OpenSearch client")
    return client


async def add_index(index: str):
    client = await get_opensearch_client()
    try:
        response = client.indices.create(index=index, body={})
        logger.trace(f"Added index={index}, response={response}")
    except RequestError as re:
        if re.error == "resource_already_exists_exception":
            logger.trace(f"index={index} already exists, no need to create")
        else:
            logger.error(f"Exception creating index={index}, exception={re}")
            raise


async def add_document(index: str, document: dict):
    client = await get_opensearch_client()
    response = client.index(index=index, body=document, refresh=True)
    logger.trace(f"Added document to index={index}, response={response}")


async def add_patient_document(index: str, message: dict, data: Any):
    client = await get_opensearch_client()

    if message["data_format"] == "FHIR-R4":
        patient_id = data.dict()["id"]
    else:
        logger.trace(f"Can't index unsupported document type: {message['data_format']}")
        return

    document = {
        "patient_id": patient_id,
        "data_record_location": message["data_record_location"],
        "ipfs_uri": message["ipfs_uri"],
    }
    response = client.index(index=index, body=document, refresh=True)
    logger.trace(
        f"Added document for patient id={patient_id} to index={index}, response={response}"
    )


async def search_by_patient_id(index: str, patient_id: str) -> Optional[dict]:
    client = await get_opensearch_client()
    query = {"query": {"term": {"patient_id": patient_id}}}
    response = client.search(body=query, index=index)
    logger.trace(
        f"Search results for patient_id={patient_id} in index={index}: {response}"
    )
    return response


async def delete_document(index: str, doc_id: str):
    client = await get_opensearch_client()
    response = client.indices.delete(index=index)
    logger.trace(
        f"Deleted document with id={doc_id} from index={index}, response={response}"
    )


async def delete_index(index: str):
    client = await get_opensearch_client()
    response = client.indices.delete(index=index)
    logger.trace(f"Deleted index={index}, response={response}")
