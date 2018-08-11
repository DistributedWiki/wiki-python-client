import concurrent
import logging
import time
from concurrent.futures import ProcessPoolExecutor

import base58
import ipfsapi

import common.utils as utils

LOG = logging.getLogger('ipfs')


class IPFSClient:
    """
    Wrapper for ipfs_api
    """
    def __init__(self):
        self.process_pool = ProcessPoolExecutor(1)

        while True:
            try:
                self.ipfs_api = ipfsapi.connect('127.0.0.1', 5001)
                LOG.info('Connected to IPFS daemon')
                break
            except ipfsapi.exceptions.ConnectionError:
                LOG.debug('Waiting for ipfsd to get up...')
                time.sleep(1)

    # we remove 2 most significant bytes (they are always 1220)
    # when reading from smart contract, this 2 bytes must be appended back to ipfs address
    @staticmethod
    def _strip_ipfs_address(address):
        return base58.b58decode(address)[2:]

    @staticmethod
    def _restore_ipfs_address(address):
        return base58.b58encode(b'\x12\x20' + address).decode()

    def add_article(self, path):
        result = self.ipfs_api.add(path)
        address = result['Hash']

        LOG.info('Article added to ipfs: ipfs_address=%s', address)

        return self._strip_ipfs_address(address)

    def get_article(self, id, timeout):
        try:
            id = self._restore_ipfs_address(id)

            # get function could potentially never complete (when resource is not hosted by anyone)
            utils.run_with_timeout(self.process_pool, timeout, self.ipfs_api.get, id)

            return id
        except concurrent.futures.TimeoutError as e:
            raise TimeoutError('IPFS action timed out')