import logging
import os
import ipfsapi
import time
import base58
from blockchain.blockchain_db import *

LOG = logging.getLogger('client')


class DWClient:
    """
    Distributed Wikipedia Client
    """
    def __init__(self):
        while True:
            try:
                self.ipfs_api = ipfsapi.connect('127.0.0.1', 5001)
                LOG.info('Connected to IPFS daemon')
                break
            except ipfsapi.exceptions.ConnectionError:
                LOG.debug('Waiting for ipfsd to get up...')
                time.sleep(1)
        self.db = BlockchainDB()

    # we remove 2 most significant bytes (they are always 1220)
    # when reading from smart contract, this 2 bytes must be appended back to ipfs address
    def _strip_ipfs_address(self, address):
        return base58.b58decode(address)[2:]

    def _restore_ipfs_address(self, address):
        return base58.b58encode(b'\x12\x20' + address).decode()

    def add_article(self, article_filepath):
        LOG.debug('Adding article sequence started')

        # TODO - we should not add exisitng files, insted, provide editor and create files ourselves
        article_ipfs = self.ipfs_api.add(article_filepath)
        ipfs_address = article_ipfs['Hash']

        # TODO - title should not be filepath
        title = os.path.basename(article_filepath)

        try:
            self.db.add_article_tx(title, self._strip_ipfs_address(ipfs_address))
            LOG.info('Article added: title=%s, ipfs_address=%s', title, ipfs_address)
        except Exception as e:
            print(e)
