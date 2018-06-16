import logging
from web3 import Web3
from web3 import HTTPProvider
import ipfsapi
import time

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
        # TODO(pkobielak): TestRPCProvider need workaround to work on Win10
        # TODO(pkobielak): ganache used instead of TestRPCProvider
        self.web3 = Web3(HTTPProvider('http://localhost:8545'))

    def add_article(self, article_filepath):
        LOG.debug('Adding article sequence started')

        article_ipfs = self.ipfs_api.add(article_filepath)
        ipfs_address = article_ipfs['Hash']

        LOG.info('Article added: contract_address=%s ipfs_address=%s',
                 '', ipfs_address)
