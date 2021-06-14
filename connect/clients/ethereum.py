"""
ethereum.py

Ethereum client that provides functionality to interact with a configurable blockchain network.
Service instance is bound to data attributes and accessed through "get" functions.
"""
import asyncio
import logging
import time
from web3 import Web3
from hexbytes import HexBytes
from connect.config import get_settings
from connect.exceptions import EthereumNetworkConnectionError
from threading import Thread
from typing import Callable, List, Optional


logger = logging.getLogger(__name__)
# client instances
eth_client = None

# ******************************************
# Ethereum client services
# ******************************************
class EthereumClient:
    """
    Wrapper for LFH that utilizes the Web3 library for interacting with an
    Ethereum blockchain network
    """

    def __init__(self, configs):
        self._connected = False
        self._client_connection = None
        self._eth_network_uri = configs['eth_network_uri']

        self._client_connection = Web3(Web3.HTTPProvider(self._eth_network_uri))

        if(self._client_connection and self._client_connection.isConnected()):
            logger.info(f"Connected to the Ethereum network at: {self._eth_network_uri}")
            self._connected = True
        else:
            error_msg = f"Failed to connect to the Ethereum network at: {self._eth_network_uri}"
            self._connected = False
            logger.error(error_msg)
            raise EthereumNetworkConnectionError(error_msg)

    def get_block_info(self, block_num=None):
        if not self._connected:
            error_msg = "Failed to retrieve block information - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            if block_num:
                block_info_dict = dict(self._client_connection.eth.get_block(block_num))
            else:
                block_info_dict = dict(self._client_connection.eth.get_block('latest'))

            return json.dumps(block_info_dict, cls=HexJsonEncoder)

    def get_latest_block_number(self, block_num: int) -> int:
        if not self._connected:
            error_msg = "Failed to retrieve latest block number - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            return self._client_connection.eth.block_number

    def set_default_account_num(self, account_num: str):
        if not self._connected:
            error_msg = "Failed to set default account number - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            self._client_connection.eth.default_account = account_num

    def get_all_account_nums(self):
        if not self._connected:
            error_msg = "Failed to retrieve account numbers - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            return self._client_connection.eth.get_accounts()

    def get_balance_for_account_num(self, account_num: str) -> int:
        if not self._connected:
            error_msg = "Failed to retrieve account balance - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            return self._client_connection.eth.get_balance(account_num)

    def get_transaction_info(self, tx_hash: str):
        if not self._connected:
            error_msg = "Failed to retrieve transaction info - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            tx_info_dict = dict(self._client_connection.eth.get_transaction(tx_hash))
            return json.dumps(tx_info_dict, cls=HexJsonEncoder)

    def get_gas_price(self) -> int:
        if not self._connected:
            error_msg = "Failed to retrieve gas price - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            return self._client_connection.eth.gas_price()

    def send_transaction(self, from_account: str, to_account: str, gas: int = None,
                         gas_price: int = None, value: int = None, data,
                         nonce: int = None) -> str:
        '''
        Signs and sends a transaction

        If the transaction specifies a data value but does not specify gas then the gas value
        will be populated using the estimate_gas() function with an additional buffer of 100000
        gas up to the gasLimit of the latest block.
        In the event that the value returned by estimate_gas() method is greater than the
        gasLimit a ValueError will be raised.

        :param from_account: The address the transaction is sent from. Optionally uses a default account.
        :param to_account: The address the transaction is directed to. Optional when creating new contract.
        :param gas: Optional. Gas provided for the transaction execution. It will return unused gas.
        :param gas_price: Optional. Integer gas_price used for each paid gas.
        :param value: Optional. Integer value sent with this transaction.
        :param data: The compiled code of a contract OR the hash of the invoked method signature and encoded parameters.
        :param nonce: Optional. This allows to overwrite your own pending transactions that use the same nonce.
        '''
        if not self._connected:
            error_msg = "Failed to send off transaction - connection error"
            raise EthereumNetworkConnectionError(error_msg)
        else:
            # The transaction parameter should be a dictionary for the Web3 API.
            transaction = {
                'from': from_account,
                'to': to_account
            }

            if gas:
                transaction['gas'] = gas
            if gas_price:
                transaction['gas_price'] = gas_price
            if value:
                transaction['value'] = value
            if nonce:
                transaction['nonce'] = nonce

            logger.info(f"transaction information: {transaction}")
            return self._client_connection.eth.send_transaction(transaction).hex()


def get_ethereum_client() -> Optional[EthereumClient]:
    """
    :return: a connected EthereumClient instance
    """
    global eth_client
    if not eth_client:
        settings = get_settings()
        eth_client_config = {
            "eth_network_uri": settings.ethereum_network_uri
        }
        eth_client = EthereumClient(
            configs=eth_client_config
        )

    return eth_client


class HexJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)
