import hashlib
import logging
import os
import time

import base58
import ipfsapi

from blockchain.blockchain_db import BlockchainDB

LOG = logging.getLogger('client')


def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda: f.read(128 * 1024), b''):
            h.update(b)
    return h.hexdigest()


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

    def add_article(self, title, article_filepath):
        LOG.debug('Adding article sequence started')

        article_ipfs = self.ipfs_api.add(article_filepath)
        ipfs_address = article_ipfs['Hash']

        try:
            self.db.add_article_tx(title, self._strip_ipfs_address(ipfs_address))
            LOG.info('Article added: title=%s, ipfs_address=%s', title, ipfs_address)
        except Exception as e:
            print(e)

    def get_article(self, title):
        LOG.debug('Get article')

        article_id = self.db.get_article_ID(title)
        article_id = self._restore_ipfs_address(article_id)
        self.ipfs_api.get(article_id)

        # Todo - this can be checked before downloading ???
        # Check if local file exists and is up-to-date
        if os.path.exists(title) and file_hash(article_id) != file_hash(title):
            os.remove(title)
            os.rename(article_id, title)
        elif not os.path.exists(title):
            os.rename(article_id, title)
        else:
            os.remove(article_id)

