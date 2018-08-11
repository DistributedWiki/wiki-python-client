import datetime
import logging

LOG = logging.getLogger('article_version_history')


class ArticleVersionHistory:
    def __init__(self, article_title, client):
        self.article_title = article_title
        self.client = client
        self.history = client.get_article_history(article_title)
        LOG.info('Article version history initialized for: %s', article_title)

    def reload_article_history(self):
        self.history = self.client.get_article_history(self.article_title)
        LOG.info('Article version history reloaded for: %s', self.article_title)

    def get_versions_list(self):
        """
        Makes list of strings.
        :return: list of strings
        """
        LOG.debug('Making versions list of article: %s', self.article_title)
        versions_data = self.client.get_article_history(self.article_title)
        history_list = []
        for i, version_dict in enumerate(versions_data):
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
                  index, self.article_title)
        content = self.client.get_article(
            title=self.article_title,
            version_ipfs_address=self.history[index]['ID']
        )
        LOG.debug('content: %s', content)
        return content
