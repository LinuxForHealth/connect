### Using an Ethereum Blockchain network with `connect`
`connect` can be configured to work with any blockchain network that exposes an HTTP endpoint. The Truffle Suite with [Ganache](https://www.trufflesuite.com/ganache) offers an easy 1-click blockchain setup for development and testing.

Use the RPC Server address specified by Ganache or another deployed blockchain as the `ethereum_network_uri` in [`config.py`](https://github.com/LinuxForHealth/connect/blob/main/connect/config.py)
![image](https://user-images.githubusercontent.com/21041723/122135142-2a001300-cdfd-11eb-8a1b-c0722ddb726a.png)


Using the `get_ethereum_client` utility function instantiates `EthereumClient` and returns the instance for convenience. We use this code pattern extensively for all client functionality included with `connect`.

### Supported client operations
- Get block info
- Get latest block number
- Set default account number for all transactions
- Get all account numbers
- Create a new account
- Get account info for a private key
- Get balance for an account number
- Get transaction info
- Get gas price
- Send a transaction
- Send a raw transaction
- Contract deployment **TODO
