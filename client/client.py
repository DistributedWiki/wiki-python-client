import datetime
import logging
import os
import sys

import common.utils as utils
from blockchain.blockchain_db import BlockchainDB
from ipfs.ipfs_client import IPFSClient

LOG = logging.getLogger('client')


class DWClient:
    """
    Distributed Wikipedia Client
    """
    def __init__(self, eth_private_key, eth_provider, top_level_address):
        self.blockchain_db = BlockchainDB(eth_private_key, eth_provider,
                                          top_level_address)

        self.ipfs = IPFSClient()
        self.titles = []

        self.current_article_title = None
        self.history = None

    def get_unprocessed_tx(self, number=sys.maxsize):
        return self.blockchain_db.get_tx_list(number)

    def get_transaction_price(self):
        return self.blockchain_db.estimate_add_article_tx()

    def initialize_article_data(self, title):
        self.current_article_title = title
        self.history = self._get_article_history(title)
        LOG.info('Article version history initialized for: %s', title)

    def article_exists(self, title):
        return self.blockchain_db.article_exists(title)

    def add_article(self, title, article_filepath, authorized, allow_author):
        LOG.debug('Adding article to IPFS')

        if self.blockchain_db.article_exists(title):
            raise Exception("Article exists")

        if allow_author:
            authorized.append(self.blockchain_db.get_account_address())

        # Remove duplicates if any
        authorized = list(set(authorized))

        ipfs_address = self.ipfs.add_article(article_filepath)
        self.blockchain_db.add_article_tx(title, ipfs_address, authorized)

        LOG.debug("Article added to IPFS")
        LOG.debug("Adding article to smart contract")

    def update_article(self, title, article_filepath):
        LOG.debug('Updating article to IPFS')

        if not self.blockchain_db.article_exists(title):
            raise Exception("Article doesn't exist")

        ipfs_address = self.ipfs.add_article(article_filepath)
        self.blockchain_db.update_article_tx(title, ipfs_address)

        LOG.debug("Article updated to IPFS")
        LOG.debug("Updating article on smart contract")

    def get_article(self, title, version_ipfs_address=None):
        LOG.debug('Get article')

        if version_ipfs_address is not None:
            partial_ipfs_address = version_ipfs_address
        else:
            partial_ipfs_address = self.blockchain_db.get_article_ID(title)
        full_ipfs_address = self.ipfs.get_article(partial_ipfs_address, 20)

        # Todo - this can be checked before downloading ???
        # Check if local file exists and is up-to-date
        if (os.path.exists(title)
                and utils.file_hash(
                    full_ipfs_address) != utils.file_hash(title)):
            os.remove(title)
            os.rename(full_ipfs_address, title)
        elif not os.path.exists(title):
            os.rename(full_ipfs_address, title)
        else:
            os.remove(full_ipfs_address)

        path = os.path.join(utils.get_prefix_path(), title)
        article_content_file = open(path)
        article_content = article_content_file.read()
        article_content_file.close()
        return article_content

    def get_titles(self):
        titles_to_fetch = self.blockchain_db.get_number_of_titles() \
                          - len(self.titles)
        while titles_to_fetch > 0:
            article_title_proposition = self.blockchain_db.get_title(
                len(self.titles)
            ).strip('\x00')
            self.titles.append(article_title_proposition)
            titles_to_fetch -= 1

        return self.titles

    def get_versions_list(self):
        """
        Makes list of strings for gui.
        :return: list of strings
        """
        LOG.debug('Making versions list of article: %s',
                  self.current_article_title)
        if self.current_article_title is None:
            LOG.error('Article data is not initialized. Stopping function '
                      'execution...')
            return None
        history_list = []
        for i, version_dict in enumerate(self.history):
            date = datetime.datetime.fromtimestamp(
                int(version_dict['timestamp'])
            ).strftime('%Y-%m-%d %H:%M:%S')
            history_list.append("{}:: Time: {}".format(i, date))

        return history_list

    def get_version_by_index(self, index):
        """
        Returns content of article version by its index.
        :param index:
        :return: text
        """
        LOG.debug('Getting version[%s] content of article: %s',
                  index, self.current_article_title)
        if self.current_article_title is None:
            LOG.error('Article data is not initialized. Stopping function '
                      'execution...')
            return None
        content = self.get_article(
            title=self.current_article_title,
            version_ipfs_address=self.history[index]['ID']
        )
        if len(content) < 250:
            LOG.debug('content: %s', content)
        else:
            LOG.debug('content: too long to log, written only to preview')
        return content

    def _get_article_history(self, title):
        """
        Retrieves article data from blockchain.
        :param title:
        :return: list of article versions data
        """
        LOG.debug('Retrieving article version history...')
        history_length = self.blockchain_db.get_number_of_modifications(title)
        article_version_history = []
        for version_index in range(history_length):
            version_info = self.blockchain_db.get_modification_info(
                title, version_index)
            article_version_history.append(version_info)

        return article_version_history
