"""
opensearch.py
OpenSearch client wrapper
"""
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
    """
    Create a new index.
    """
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
    """
    Add a document to an index.
    :param index: Name of the index to add the document to
    :param document: The dict specifying the document to add.
        For example, to add a patient document for a patient with id = "001"
        and kafka and ipfs storage locations, use:
        {
            "patient_id": "001"",
            "data_record_location": message["data_record_location"],
            "ipfs_uri": message["ipfs_uri"],
        }
        where the LinuxForHealth message[] contains the kafka and ipfs data storage locations.
    :return:
    """
    client = await get_opensearch_client()
    response = client.index(index=index, body=document, refresh=True)
    logger.trace(f"Added document to index={index}, response={response}")


async def search_by_query(index: str, query: dict) -> Optional[dict]:
    """
    Search via a provided query.
    :param index: Name of the index to search
    :param query: The dict specifying the query search terms.
        For example, to search an index for a patient_id of "001", use:
        {"query": {"term": {"patient_id": "001"}}}
    :return: dict containing the search results
    """
    client = await get_opensearch_client()
    response = client.search(body=query, index=index)
    logger.trace(f"Search results for query={query} in index={index}: {response}")
    return response


async def delete_document(index: str, doc_id: str):
    """
    Delete a document from an index.
    :param index: Name of the index to add the document to
    :param doc_id: Id of the document to delete

    One way to use this method is to first query for records, then use the
    query results to get the ids of the documents to delete.
    """
    client = await get_opensearch_client()
    response = client.delete(index=index, id=doc_id)
    logger.trace(
        f"Deleted document with id={doc_id} from index={index}, response={response}"
    )


async def delete_index(index: str):
    """
    Delete an index.
    :param index: Name of the index to delete
    """
    client = await get_opensearch_client()
    response = client.indices.delete(index=index)
    logger.trace(f"Deleted index={index}, response={response}")
