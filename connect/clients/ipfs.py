"""
ipfs.py

IPFS client services that support REST calls for persistence of records with an
IPFS cluster
"""
import base64
import logging
import httpx
import json
from connect.config import get_settings
from connect.support.encoding import ConnectEncoder, decode_to_str
from tempfile import NamedTemporaryFile
from typing import Any, Tuple


logger = logging.getLogger(__name__)
_ipfs_client = None


class IPFSClient:
    """
    IPFS client services for persistence.  Uses the IPFS cluster
    REST API (https://cluster.ipfs.io/documentation/reference/api/)
    for all URIs that don't begin with /api/v0 and the IPFS
    HTTP API (https://docs.ipfs.io/reference/http/api/) for URIs
    starting with /api/v0.
    """

    def __init__(self, cluster_uri, http_uri, replication_factor):
        self._uri = cluster_uri
        self._http_uri = http_uri
        self._replication_factor = replication_factor
        self._add_uri = self._uri + "/add"
        self._get_peers_uri = self._uri + "/peers"
        self._unpin_cid_uri = self._uri + "/pins/"
        self._cat_uri = self._http_uri + "/api/v0/cat"

    async def persist_json_to_ipfs(self, payload: dict) -> Tuple[int, str]:
        """
        Allows persistence of JSON payloads (as a dict) into an IPFS cluster
        The IPFS cluster instance being connected to is configurable.

        Content is pinned by default during the add operation.

        :param payload: dict containing the message to be persisted to IPFS
        :returns: Tuple containing an HTTP response code and an unique ID
                  addressing the content added to the IPFS cluster. Returns
                  response code and None if a non 200 response code is returned
                  from the IPFS Cluster.
        """
        if not payload:
            error_msg = "dict payload not provided for persistence into IPFS"
            logger.error(error_msg)
            raise ValueError(error_msg)

        async with httpx.AsyncClient() as client:
            try:
                with NamedTemporaryFile(mode="w+") as payload_temp_file:
                    json.dump(payload, payload_temp_file, cls=ConnectEncoder)
                    payload_temp_file.flush()
                    temp_file_name = payload_temp_file.name

                    files = {
                        "upload-file": (
                            temp_file_name,
                            open(temp_file_name, "r"),
                            "application/json",
                        )
                    }
                    response = await client.post(self._add_uri, files=files)
                    response_code = response.status_code

                if response_code == 200:
                    result = response.text.split("\n")
                    result_first = json.loads(result[0])
                    logger.trace(
                        f"Successfully added and pinned to IPFS, cid: {result_first['cid']['/']}"
                    )
                    return response_code, result_first["cid"]["/"]
                else:
                    logger.error(
                        f"Error persisting to IPFS HTTP response_code: {response.status_code}"
                    )
                    return response_code, None
            except Exception as ex:
                logger.error(
                    f"Exception raised while persisting to the IPFS Cluster: {ex}"
                )
                return 500, None

    async def get_object_from_ipfs(self, path: str) -> dict:
        """
        Retrieves a JSON payload (as a dict) from an IPFS cluster

        :param path: The IPFS path for the object to retrieve
        :returns: Object (dict) stored in IPFS.
        """
        if not path:
            error_msg = "IPFS path not provided for retrieval from IPFS"
            logger.error(error_msg)
            raise ValueError(error_msg)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self._cat_uri}?arg={path}")
                response_code = response.status_code

                if response_code == 200:
                    result = json.loads(response.text)
                    logger.trace(f"Successfully retrieved from IPFS: {result}")
                    return {"response_code": response_code, "document": result}
                else:
                    logger.error(
                        f"Error retrieving from IPFS, HTTP response code: {response.status_code}"
                    )
                    return {"response_code": response_code, "document": None}
            except Exception as ex:
                logger.error(f"Exception raised while retrieving from IPFS: {ex}")
                return {"response_code": 500, "document": None}

    async def get_ipfs_cluster_peers(self) -> Tuple[int, Any]:
        """
        Returns a list of all connected IPFS Cluster Peers.
        Note: IPFS Node Peers are managed implicitly by IPFS Cluster.

        :returns: Tuple containing an HTTP response code and JSON with IPFS
                  Cluster and managed Nodes information. Returns response_code
                  and None if a non 200 response code is returned from IPFS
                  Cluster
        """
        async with httpx.AsyncClient() as client:
            response = client.get(self._get_peers_uri)

            if response.status_code == 200:
                logger.trace("Successfully retrieved IPFS Cluster peers")
                return response.status_code, response.json()
            else:
                logger.error(
                    f"Error retrieving IPFS Cluster peers; Response code: {response.status_code}"
                )
                return response.status_code, None

    async def unpin_content_from_cluster(self, content_cid) -> bool:
        """
        Unpins content from the IPFS cluster
        :param content_cid

        :returns: Returns a tuple containing an HTTP response code and a boolean
                  value indicating the success or failure while unpinning
                  content.
        """
        if not content_cid:
            error_msg = "content_cid parameter not provided for unpinning"
            logger.error(error_msg)
            raise ValueError(error_msg)

        _unpin_uri = self._unpin_cid_uri + content_cid

        async with httpx.AsyncClient() as client:
            response = client.delete(_unpin_uri)
            if response.status_code == 200:
                logger.trace(f"Unpinned cid: {content_cid} from IPFS Cluster")
                return response.status_code, True
            else:
                logger.error(
                    f"Error unpinning content from IPFS Cluster; Response_code: {response.status_code}"
                )
                return response.status_code, False


def get_ipfs_cluster_client() -> IPFSClient:
    global _ipfs_client

    if not _ipfs_client:
        settings = get_settings()

        _ipfs_client = IPFSClient(
            settings.ipfs_cluster_uri,
            settings.ipfs_http_uri,
            settings.ipfs_cluster_replication_factor,
        )

    return _ipfs_client
