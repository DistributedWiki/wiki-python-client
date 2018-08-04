import logging
import os

from blockchain.blockchain_db import BlockchainDB
import common.utils as utils
from ipfs.ipfs_client import IPFSClient

LOG = logging.getLogger('client')


class DWClient:
    """
    Distributed Wikipedia Client
    """
    def __init__(self, eth_private_key, eth_provider):
        self.db = BlockchainDB(eth_private_key, eth_provider)

        self.ipfs = IPFSClient()
        self.titles = []

    def add_article(self, title, article_filepath):
        LOG.debug('Adding article sequence started')

        if self.db.article_exists(title):
            raise Exception("Article exists")

        try:
            ipfs_address = self.ipfs.add_article(article_filepath)
            self.db.add_article_tx(title, ipfs_address)
            LOG.info('Article added to smart contract: title=%s, ipfs_address=%s',
                     title, ipfs_address)
        except Exception as e:
            print(e)

    def update_article(self, title, article_filepath):
        LOG.debug('Updating article contract...')

        try:
            ipfs_address = self.ipfs.add_article(article_filepath)
            self.db.update_tx(title, ipfs_address)
            LOG.info('Article updated: title=%s, ipfs_address=%s',
                     title, ipfs_address)
        except Exception as e:
            print(e)

    def get_article(self, title):
        LOG.debug('Get article')

        article_id = self.db.get_article_ID(title)
        full_id = self.ipfs.get_article(article_id, 20)

        # Todo - this can be checked before downloading ???
        # Check if local file exists and is up-to-date
        if (os.path.exists(title)
                and utils.file_hash(full_id) != utils.file_hash(title)):
            os.remove(title)
            os.rename(full_id, title)
        elif not os.path.exists(title):
            os.rename(full_id, title)
        else:
            os.remove(full_id)

    def get_titles(self):
        titles_to_fetch = self.db.get_number_of_titles() - len(self.titles)
        while titles_to_fetch > 0:
            self.titles.append(self.db.get_title(len(self.titles)))
            titles_to_fetch -= 1

        return self.titles

    def get_article_history(self, title):
        LOG.debug('Retrieving article version history...')
        history_length = self.db.get_number_of_modifications(title)
        article_version_history = []
        for version_index in range(history_length):
            version_info = self.db.get_modification_info(title, version_index)
            article_version_history.append(version_info)

        return article_version_history
