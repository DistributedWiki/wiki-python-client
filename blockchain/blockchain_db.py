from web3 import Web3, HTTPProvider

import blockchain.article_abi as article_abi
import blockchain.contracts_conf as cfg
import blockchain.top_level_abi as top_level_abi


class BlockchainDB:
    def __init__(self,
                 provider=HTTPProvider(cfg.infura_endpoint),
                 address=cfg.account_address,
                 private_key=cfg.private_key,
                 top_level_address=cfg.top_level_address):
        self.w3 = Web3(provider)
        self.address = address
        self.private_key = private_key # TODO - this is not safe
        self.top_level_contract = self.w3.eth.contract(address=top_level_address, abi=top_level_abi.abi)

    def _hash(self, data_str):
        return self.w3.sha3(text=data_str).hex()

    def _get_article_contract(self, title):
        title_hash_bytes32 = self.w3.toBytes(hexstr=self._hash(title))

        return self.w3.eth.contract(
            address=self.top_level_contract.functions.getArticle(title_hash_bytes32).call(),
            abi=article_abi.abi
        )

    def get_article_ID(self, title):
        """
        :param title: string
        """
        return self._get_article_contract(title).functions.getArticleID().call()

    def add_article_tx(self, title, ID):
        """
        :param title: string
        :param ID: bytes
        """
        title_hash_bytes32 = self.w3.toBytes(hexstr=self._hash(title))

        # TODO - parametrize gas
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.address), 'gas': 1400000}
        tx = self.top_level_contract.functions.createArticle(
            title_hash_bytes32,
            ID
        ).buildTransaction(tx_dict)

        signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

        # TODO: async?
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        if int(receipt['status']) == 0:
            raise Exception('transaction failed')

    def update_tx(self, title, newID):
        """
        :param title: string
        :param newID: bytes
        """
        article_contract = self._get_article_contract(title)

        # TODO - parametrize gas
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.address), 'gas': 140000}
        tx = article_contract.functions.update(newID).buildTransaction(tx_dict)

        signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

        # TODO: async?
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        if int(receipt['status']) == 0:
            raise Exception('transaction failed')

    def get_number_of_modifications(self, title):
        return self._get_article_contract(title).functions.nModifications().call()

    def get_modification_info(self, title, index):
        if index >= self.get_number_of_modifications(title) or index < 0:
            raise IndexError

        ID_bytes32, address, timestamp = self._get_article_contract(title).functions.commits(index).call()

        return {
            'ID': self.w3.toHex(ID_bytes32),
            'address': address,
            'timestamp': timestamp
        }
