"""
ipfs.py

IPFS client services that support REST calls for persistence of records with an
IPFS cluster
"""
import logging
import httpx
import json
from tempfile import NamedTemporaryFile
from connect.config import get_settings


logger = logging.getLogger(__name__)
_ipfs_client = None


# ******************************************
# IPFS client services for persistence
# ******************************************
class IPFSClient:
    def __init__(self, uri, replication_factor):
        self._uri = uri
        self._replication_factor = replication_factor
        self._add_uri = self._uri + "/add"
        self._get_peers_uri = self._uri + "/peers"
        self._unpin_cid_uri = self._uri + "/pins/"

    async def persist_json_to_ipfs(self, payload_dict):
        """
        Allows persistence of JSON payloads (as a dict) into an IPFS cluster
        The IPFS cluster instance being connected to is configurable.

        Content is pinned by default during the add operation.

        :param payload_dict
        :returns: Tuple containing an HTTP response code and an unique ID
                  addressing the content added to the IPFS cluster. Returns
                  response code and None if a non 200 response code is returned
                  from the IPFS Cluster.
        """
        response = None

        if not payload_dict:
            error_msg = "dict payload not provided for persistence into IPFS"
            logger.error(error_msg)
            raise ValueError(error_msg)

        async with httpx.AsyncClient() as client:
            try:
                with NamedTemporaryFile() as payload_temp_file:
                    json.dump(payload_dict, payload_temp_file)
                    payload_temp_file.flush()
                    temp_file_name = payload_temp_file.name

                    files = {
                        "upload-file": (
                            temp_file_name,
                            open(temp_file_name, "r"),
                            "multipart/form-data",
                        )
                    }
                    response = await client.post(self._add_uri, files=files)
                    response_code = response.status_code

                if response_code == 200:
                    response_dict = json.loads(response.json())
                    info_msg = (
                        "Successfully added and pinned to IPFS -- "
                        + f"cid: {response_dict['cid']}"
                    )
                    logger.info(info_msg)
                    return (response_code, response_dict)
                else:
                    error_msg = (
                        "Error persiting to IPFS;"
                        + f"HTTP response_code: {response.status_code}"
                    )
                    logger.error(error_msg)
                    return (response_code, None)
            except:
                error_msg = "Exception raised while persisting to the IPFS Cluster"
                raise Exception(error_msg)

    async def get_ipfs_cluster_peers(self):
        """
        Returns a list of all connected IPFS Cluster Peers.
        Note: IPFS Node Peers are managed implicitly by IPFS Cluster.

        :returns: Tuple containing an HTTP response code and JSON with IPFS
                  Cluster and managed Nodes information. Returns reponse_code
                  and None if a non 200 response code is returned from IPFS
                  Cluster
        """
        async with httpx.AsyncClient() as client:
            response = client.get(self._get_peers_uri)

            if response.status_code is 200:
                info_msg = "Successfully retrieved IPFS Cluster peers"
                logger.info(info_msg)
                return (response.status_code, response.json())
            else:
                error_msg = (
                    f"Error on retrieving IPFS Cluster peers; "
                    + f"HTTP response_code: {response.status_code}"
                )
                logger.error(error_msg)
                return (response.status_code, None)

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
                info_msg = f"Unpinned cid: {content_cid} from IPFS Cluster"
                logger.info(info_msg)
                return (response.status_code, True)
            else:
                error_msg = (
                    "Error unpinning content from IPFS Cluster;"
                    + f"HTTP response_code: {response.status_code}"
                )
                logger.error(error_msg)
                return (response.status_code, False)


def get_ipfs_cluster_client() -> IPFSClient:
    global _ipfs_client

    if not _ipfs_client:
        settings = get_settings()

        _ipfs_client = IPFSClient(
            settings.ipfs_cluster_uri, settings.ipfs_cluster_replication_factor
        )

    return _ipfs_client
