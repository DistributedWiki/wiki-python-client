import logging
import os
import subprocess
import sys

from PyQt5.Qt import QSize
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMainWindow

import client.gui.gui_conf as gc
import common.utils as utils
from client.client import DWClient
from client.client_conf import DEV_TOP_LEVEL_ADDRESS
from client.gui.worker import Worker
from client.login import Login

LOG = logging.getLogger('gui')


class GUI(QMainWindow):
    """
    GUI for Distributed Wikipedia Client
    """
    def __init__(self):
        super().__init__()
        self.resize(gc.FRAME_WIDTH, gc.FRAME_HEIGHT)
        self.move(
            gc.FHD_W/2 - gc.FRAME_WIDTH/2, gc.FHD_H/2 - gc.FRAME_HEIGHT/2
        )
        self.setWindowTitle(gc.WINDOW_TITLE)

        self.client = None
        self._constructUI()
        self.worker = None
        self.article_version_history = None

        os.chdir(utils.get_prefix_path())

    def _show_articles_list(self, articles, prefix):
        for article in articles:
            if prefix in article:
                self.articles_list.addItem(article)
        self.articles_list.show()

    def _constructUI(self):
        status_title = QLabel("FullNode:", self)
        status_title.move(50, 510)

        status_variable = QLabel("active", self)
        status_variable.setStyleSheet("QLabel {color: green;}")
        status_variable.move(100, 510)

        self.top_level = QLabel(
            "Current top level address: " + DEV_TOP_LEVEL_ADDRESS, self
        )

        self.top_level.resize(QSize(400, 25))
        self.top_level.move(50, 20)

        self.title_edit = QLineEdit(
            self,
            placeholderText='Put unique article title here'
        )

        self.title_edit.resize(QSize(250, 25))
        self.title_edit.move(50, 50)

        self.btn_update_article = QPushButton('Update article', self)
        self.btn_update_article.resize(QSize(90, 25))
        self.btn_update_article.move(510, 50)
        self.btn_update_article.clicked.connect(self._update_article_action)

        # This button is active only when article is selected.
        self.btn_update_article.setDisabled(True)

        btn_search_article = QPushButton('Search article', self)
        btn_search_article.resize(QSize(90, 25))
        btn_search_article.move(310, 50)
        btn_search_article.clicked.connect(self._search_article_action)

        btn_add_article = QPushButton('Add article', self)
        btn_add_article.resize(QSize(90, 25))
        btn_add_article.move(410, 50)
        btn_add_article.clicked.connect(self._add_article_action)

        version_history_label = QLabel("Version history", self)
        version_history_label.move(410, 95)

        self.version_history_list = QListWidget(self)
        self.version_history_list.resize(QSize(350, 100))
        self.version_history_list.move(410, 120)
        self.version_history_list.itemClicked.connect(
            self._show_clicked_article_version
        )

        content_editor_label = QLabel("Content viewer", self)
        content_editor_label.move(410, 225)

        self.article_content_editor = QPlainTextEdit(self, readOnly=True)
        self.article_content_editor.resize(QSize(350, 250))
        self.article_content_editor.move(410, 250)

        articles_list_label = QLabel("Articles", self)
        articles_list_label.move(50, 95)

        self.articles_list = QListWidget(self)
        self.articles_list.resize(QSize(350, 380))
        self.articles_list.move(50, 120)

        self.articles_list.show()
        self.articles_list.itemClicked.connect(self._get_article_action)

        self.statusBar().showMessage('Connected')

    def _set_app_status(self, text):
        self.statusBar().showMessage(
            'Status: {}'.format(text)
        )

    def _show_clicked_article_version(self, item):
        LOG.info('_show_clicked_article_version')
        LOG.info('clicked article version: %s', item.text())
        self._set_app_status(
            'Loading preview of article {}'.format(item.text())
        )
        article_version_id = int(item.text().split('::')[0])
        article_content = self.client.get_version_by_index(
            article_version_id
        )
        self.article_content_editor.clear()
        self.article_content_editor.insertPlainText(article_content)
        self._set_app_status(
            'Loaded preview of article {}'.format(item.text())
        )

    def _client_action_failed(self, cause):
        self._set_current_article_title("<none>")
        self._set_app_status('Error occurred: {}'.format(cause))

    def _update_article_action_success(self, title):
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._set_app_status('Article updated successfully')

    def _update_article_action(self):
        LOG.info('_update_article_action called')
        self._set_app_status('Updating article...')
        title = self.title_edit.text()
        if title is None:
            LOG.error('Article title is not set. Please load article first.')
            return
        path = self._open_file(title)
        self._set_app_status(
            'Synchronizing article with distributed systems...'
        )

        self.worker = Worker(self.client.update_article, title, path)
        self.worker.signal_finished.connect(
            lambda: self._update_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def _open_file(self, filename):
        """
        Opens file with provided filename in default system editor.
        Creates file if it doesn't exists.
        """
        self._set_app_status('Opening file...')
        path = os.path.join(utils.get_prefix_path(), filename)
        utils.create_file_if_not_exists(path)

        print(path)

        if os.name == 'nt':
            subprocess.call(('notepad.exe', path))  # XXX: select editor...
        elif os.name == 'posix':
            subprocess.call(('xdg-open', path))
        self._set_app_status('File closed')
        return path

    def _add_article_action_success(self, title):
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._set_app_status('Article added successfully')

    def _add_article_action(self):
        LOG.debug('_add_article_action called')
        self._set_app_status('Adding an article...')
        title = self.title_edit.text()
        path = self._open_file(title)
        self._set_app_status(
            'Synchronizing article with distributed systems...'
        )

        self.worker = Worker(self.client.add_article, title, path)
        self.worker.signal_finished.connect(
            lambda: self._add_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def _get_article_action_success(self, title):
        self.client.initialize_article_data(title)

        self.btn_update_article.setDisabled(False)

        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._set_app_status(
            'Data for an article: \"{}\" has finished loading'.format(title)
        )

    def _get_article_action(self, title):
        title = title.text()
        LOG.debug('_get_article_action called with title: {}'.format(title))
        self._set_app_status('Loading data for an article: {}'.format(title))
        self.title_edit.setText(title)

        self.article_content_editor.clear()
        self.version_history_list.clear()

        self.worker = Worker(self.client.get_article, title)
        self.worker.signal_finished.connect(
            lambda: self._get_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def _search_article_action(self):
        LOG.debug('_search_article_action called')
        self._set_app_status('Searching for an article...')
        self.articles_list.clear()
        self.article_content_editor.clear()

        title = self.title_edit.text()

        self.worker = Worker(lambda:
                             self._show_articles_list(
                                 self.client.get_titles(), title))
        self.worker.signal_finished.connect(
            lambda: self._set_app_status('Listed found articles')
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def init_client(self, eth_private_key, eth_provider, top_level_address):
        self._set_app_status('Initializing client...')
        self.client = DWClient(eth_private_key, eth_provider, top_level_address)
        self._set_app_status('Client initialized')

    def start(self, app):
        login_window = Login(self.init_client)
        login_window.exec()

        self.show()
        sys.exit(app.exec_())

    def closeEvent(self, QCloseEvent):
        self._set_app_status('Closing application...')
        utils.kill_ipfsd_processes()
        # Delete GUI session
        self.deleteLater()
