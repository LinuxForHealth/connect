"""
ipfs.py

IPFS client services that support REST calls for persistence of records with an
IPFS cluster
"""
import logging
import httpx
import json
from connect.config import get_settings


logger = logging.getLogger(__name__)
_ipfs_client = None


# ******************************************
# IPFS client services for persistence
# ******************************************
class IPFSClient:
    def __init__(self, ipfs_cluster_uri, ipfs_cluster_replication_factor):
        self._ipfs_cluster_uri = ipfs_cluster_uri
        self._ipfs_cluster_replication_factor = ipfs_cluster_replication_factor
        self._add_to_ipfs_cluster_uri = self._ipfs_cluster_uri + '/add'
        self._get_ipfs_cluster_peers_uri = self._ipfs_cluster_uri + '/peers'
        self._unpin_cid_ipfs_cluster_uri = self._ipfs_cluster_uri + '/pins/'

    async def persist_json_to_ipfs(self, payload_dict):
        """
        Allows persistence of JSON payloads (as a dict) into an IPFS cluster
        The IPFS cluster instance being connected to is configurable.

        Content is pinned by default during the add operation.

        :param payload_dict
        :return content_cid: A unique ID addressing the content added to the
                             IPFS cluster. Returns None if a non 200 response
                             code is returned from the IPFS Cluster.
        """
        if not payload_dict:
            error_msg = 'dict payload not provided for persistence into IPFS'
            logger.error(error_msg)
            raise ValueError(error_msg)

        async with httpx.AsyncClient() as client:
            with open('payload.json', 'w') as payload_temp_file:
                json.dump(payload_dict, payload_temp_file)

            files = {'upload-file': ('payload.json', open('payload.json', 'r'),
                     'multipart/form-data')}
            response = await client.post(self._add_to_ipfs_cluster_uri,
                                         files=files)

            if response.status_code == 200:
                response_dict = json.loads(response.json())
                info_msg = "Successfully added and pinned to IPFS -- " + \
                           f"cid: {response_dict['cid']}"
                logger.info(info_msg)
                return response_dict['cid']
            else:
                error_msg = "Error persiting to IPFS;" + \
                            f"HTTP response_code: {response.status_code}"
                logger.error(error_msg)
                return None

    async def get_ipfs_cluster_peers(self):
        """
        Returns a list of all connected IPFS Cluster Peers.
        Note: IPFS Node Peers are managed implicitly by IPFS Cluster.

        :returns: JSON with IPFS Cluster and managed Nodes information.
                  Returns None if a non 200 response code is returned from
                  IPFS Cluster
        """
        async with httpx.AsyncClient() as client:
            response = client.get(self._get_ipfs_cluster_peers_uri)

            if response.status_code is 200:
                return response.json()
            else:
                error_msg = f"Error on retrieving IPFS Cluster peers;" + \
                            f"HTTP response_code: {response.status_code}"
                logger.error(error_msg)
                return None

    async def unpin_content_from_cluster(self, content_cid):
        """
        Unpins content from the IPFS cluster
        :param content_cid

        :returns int: Returns an integer code; 0 for success; 1 for failure
        """
        if not content_cid:
            error_msg = "content_cid parameter not provided for unpinning"
            logger.error(error_msg)
            raise ValueError(error_msg)

        _unpin_uri = self._unpin_cid_ipfs_cluster_uri + content_cid

        async with httpx.AsyncClient() as client:
            response = client.delete(_unpin_uri)
            if response.status_code == 200:
                info_msg = f"Unpinned cid: {content_cid} from IPFS Cluster"
                logger.info(info_msg)
                return 0
            else:
                error_msg = "Error unpinning content from IPFS Cluster;" + \
                            f"HTTP response_code: {response.status_code}"
                logger.error(error_msg)
                return 1


def get_ipfs_cluster_client() -> IPFSClient:
    global _ipfs_client

    if not _ipfs_client:
        settings = get_settings()
        _ipfs_cluster_uri = settings.ipfs_cluster_uri
        _ipfs_cluster_replication_factor = settings.ipfs_cluster_replication_factor

        _ipfs_client = IPFSClient(_ipfs_cluster_uri,
                                  _ipfs_cluster_replication_factor)

    return _ipfs_client
