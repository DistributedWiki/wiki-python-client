import os
import threading
import pickledb

from web3 import Web3
from web3 import HTTPProvider
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy

import blockchain.article_abi as article_abi
import blockchain.top_level_abi as top_level_abi
from common.utils import get_prefix_path

DUMMY_ADDRESS = b'\xd57YkE\x9b\xdf\xf6\xdaY|$\xeb\xa7\xac\x8f\xa1\xc0&\xf4\xf0R[\xbb\xca@\xeeK\x1e\xa9\xa3B'


class BlockchainDB:
    def __init__(self,
                 private_key,
                 provider,
                 top_level_address):
        self.w3 = Web3(HTTPProvider(provider))
        self.account = self.w3.eth.account.privateKeyToAccount(private_key)
        self.top_level_contract = self.w3.eth.contract(address=top_level_address, abi=top_level_abi.abi)
        self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy)

        # Enable caching
        self.w3.middleware_stack.add(middleware.time_based_cache_middleware)
        self.w3.middleware_stack.add(middleware.latest_block_based_cache_middleware)
        self.w3.middleware_stack.add(middleware.simple_cache_middleware)

        self.lock = threading.Lock()
        self.tx_db = pickledb.load(os.path.join(get_prefix_path(),
                                         'DistWIki_DB_PendingTransactions.json'), True)

    def article_exists(self, title):
        return int(self.top_level_contract \
                   .functions \
                   .getArticle(self._encode_title(title)) \
                   .call(), 0) != 0

    def get_article_ID(self, title):
        """
        :param title: string
        """
        return self._get_article_contract(title).functions.getArticleID().call()

    def process_pending_tx(self):
        """
        Process all pending transactions and update their status
        :return: Number of pending transactions
        """
        count = 0

        for tx in self.tx_db.getall():
            status = self.tx_db.get(tx)['status']
            if status == 'pending' and self._is_tx_mined(tx):
                data = self.tx_db.get(tx)
                data['status'] = 'success' if self._get_tx_status(tx) else 'failed'
                self.tx_db.set(tx, data)
            elif status == 'pending':
                count += 1

        return count

    def get_tx_list(self, number):
        count = self.process_pending_tx()
        nonce = self.w3.eth.getTransactionCount(self.account.address)

        list = []
        for tx in self.tx_db.getall():
            if nonce + count - int(self.tx_db.get(tx)['nonce']) <= number:
                list.append({'description': self.tx_db.get(tx)['description'],
                             'status': self.tx_db.get(tx)['status']})
        return list

    def add_article_tx(self, title, ID):
        """
        :param title: string
        :param ID: bytes
        """
        n_pending = self.process_pending_tx()
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.account.address) + n_pending, 'gas': 1400000}
        tx = self.top_level_contract.functions.createArticle(
            self._encode_title(title),
            ID
        ).buildTransaction(tx_dict)

        signed_tx = self.account.signTransaction(tx)

        tx_hash = self.w3.toHex(self.w3.eth.sendRawTransaction(signed_tx.rawTransaction))
        self.tx_db.set(tx_hash, {'description': "Adding article {}".format(title),
                                 'status': 'pending',
                                 'nonce': tx_dict['nonce']})

    def update_article_tx(self, title, newID):
        """
        :param title: string
        :param newID: bytes
        """
        article_contract = self._get_article_contract(title)

        n_pending = self.process_pending_tx()
        tx_dict = {'nonce': self.w3.eth.getTransactionCount(self.account.address) + n_pending, 'gas': 1400000}
        tx = article_contract.functions.update(newID).buildTransaction(tx_dict)

        signed_tx = self.account.signTransaction(tx)

        tx_hash = self.w3.toHex(self.w3.eth.sendRawTransaction(signed_tx.rawTransaction))
        self.tx_db.set(tx_hash, {'description': "Updating article {}".format(title),
                                 'status': 'pending',
                                 'nonce': tx_dict['nonce']})

    def estimate_add_article_tx(self):
        tx_dict = {'nonce': 0, 'gas': 1400000}
        tx = self.top_level_contract.functions.createArticle(
            self._encode_title("some_title"),
            DUMMY_ADDRESS
        ).buildTransaction(tx_dict)

        return self.w3.eth.estimateGas(tx) * self.w3.eth.generateGasPrice()

    def get_number_of_modifications(self, title):
        return self._get_article_contract(title).functions.nModifications().call()

    def get_number_of_titles(self):
        return self.top_level_contract.functions.nTitles().call()

    def get_title(self, index):
        return self.w3.toText(self.top_level_contract.functions.titlesList(index).call())

    def get_modification_info(self, title, index):
        if index >= self.get_number_of_modifications(title) or index < 0:
            raise IndexError

        ID_bytes32, address, timestamp = self._get_article_contract(title) \
            .functions.commits(index).call()

        return {
            'ID': ID_bytes32,
            'address': address,
            'timestamp': timestamp
        }

    def _get_tx_cost(self, tx_hash):
        receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        if receipt is None:
            raise Exception('transaction not yet mined')

        return int(receipt['gasUsed']) * self.w3.eth.generateGasPrice()

    def _is_tx_mined(self, tx_hash):
        return self.w3.eth.getTransactionReceipt(tx_hash) is not None

    def _get_tx_status(self, tx_hash):
        receipt = self.w3.eth.getTransactionReceipt(tx_hash)

        if receipt is None:
            raise Exception('transaction not yet mined')

        return int(receipt['status'])

    def _get_article_contract(self, title):
        return self.w3.eth.contract(
            address=self.top_level_contract.functions.getArticle(
                self._encode_title(title)).call(),
            abi=article_abi.abi
        )

    def _encode_title(self, title):
        title_bytes = self.w3.toBytes(text=title)

        if len(title_bytes) > 32:
            raise Exception("Too long title (max size = 32 bytes after UTF-8 encoding)")

        return title_bytes
