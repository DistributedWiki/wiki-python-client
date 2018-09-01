from web3 import Web3, HTTPProvider

import blockchain.article_abi as article_abi
import blockchain.top_level_abi as top_level_abi


class BlockchainDB:
    def __init__(self,
                 private_key,
                 provider,
                 top_level_address):
        self.w3 = Web3(HTTPProvider(provider))
        self.account = self.w3.eth.account.privateKeyToAccount(private_key)
        self.top_level_contract = self.w3.eth.contract(address=top_level_address, abi=top_level_abi.abi)

    def _get_article_contract(self, title):
        return self.w3.eth.contract(
            address=self.top_level_contract.functions.getArticle(
                self._encode_title(title)).call(),
            abi=article_abi.abi
        )

    def article_exists(self, title):
        return int(self.top_level_contract\
                   .functions\
                   .getArticle(self._encode_title(title))\
                   .call(), 0) != 0

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

        # TODO - parametrize gas
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.account.address), 'gas': 1400000}
        tx = self.top_level_contract.functions.createArticle(
            self._encode_title(title),
            ID
        ).buildTransaction(tx_dict)

        signed_tx = self.account.signTransaction(tx)
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
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.account.address), 'gas': 140000}
        tx = article_contract.functions.update(newID).buildTransaction(tx_dict)

        signed_tx = self.account.signTransaction(tx)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)

        # TODO: async?
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        if int(receipt['status']) == 0:
            raise Exception('transaction failed')

    def get_number_of_modifications(self, title):
        return self._get_article_contract(title).functions.nModifications().call()

    def get_number_of_titles(self):
        return self.top_level_contract.functions.nTitles().call()

    def get_title(self, index):
        return self.w3.toText(self.top_level_contract.functions.titlesList(index).call())

    def get_modification_info(self, title, index):
        if index >= self.get_number_of_modifications(title) or index < 0:
            raise IndexError

        ID_bytes32, address, timestamp = self._get_article_contract(title)\
            .functions.commits(index).call()

        return {
            'ID': ID_bytes32,
            'address': address,
            'timestamp': timestamp
        }

    def _encode_title(self, title):
        title_bytes = self.w3.toBytes(text=title)

        if len(title_bytes) > 32:
            raise Exception("Too long title (max size = 32 bytes after UTF-8 encoding)")

        return title_bytes
