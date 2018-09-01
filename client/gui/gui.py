import logging
import os
import subprocess
import sys

from PyQt5.Qt import QSize
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget

import client.gui.gui_conf as gc
import common.utils as utils
from client.client import DWClient
from client.gui.worker import Worker
from client.login import Login

LOG = logging.getLogger('gui')


class GUI(QWidget):
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
        status_title.move(50, 25)

        status_variable = QLabel("active", self)
        status_variable.setStyleSheet("QLabel {color: green;}")
        status_variable.move(100, 25)

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
        version_history_label.move(410, 100)

        self.version_history_list = QListWidget(self)
        self.version_history_list.resize(QSize(250, 100))
        self.version_history_list.move(410, 120)
        self.version_history_list.itemClicked.connect(
            self._show_clicked_article_version
        )

        self.article_content_editor = QPlainTextEdit(self, readOnly=True)
        self.article_content_editor.resize(QSize(350, 270))
        self.article_content_editor.move(410, 230)

        self.articles_list = QListWidget(self)
        self.articles_list.resize(QSize(350, 400))
        self.articles_list.move(50, 100)

        self.articles_list.show()
        self.articles_list.itemClicked.connect(self._get_article_action)

    def _show_clicked_article_version(self, item):
        LOG.info('_show_clicked_article_version')
        LOG.info('clicked article version: %s', item.text())

        article_version_id = int(item.text().split('::')[0])
        article_content = self.client.get_version_by_index(
            article_version_id
        )
        self.article_content_editor.clear()
        self.article_content_editor.insertPlainText(article_content)

    def _client_action_failed(self, cause):
        self._show_warning_box(cause)
        self._set_current_article_title("<none>")

    def _update_article_action_success(self, title):
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )

    def _update_article_action(self):
        LOG.info('_update_article_action called')
        title = self.title_edit.text()
        if title is None:
            LOG.error('Article title is not set. Please load article first.')
            return
        path = self._open_file(title)

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
        path = os.path.join(utils.get_prefix_path(), filename)
        utils.create_file_if_not_exists(path)

        print(path)

        if os.name == 'nt':
            subprocess.call(('notepad.exe', path))  # XXX: select editor...
        elif os.name == 'posix':
            subprocess.call(('xdg-open', path))

        return path

    def _show_warning_box(self, warning):
        box = QMessageBox()
        box.setIcon(QMessageBox.Warning)
        box.setText(warning)
        box.setWindowTitle("Warning")
        box.exec()

    def _add_article_action_success(self, title):
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )

    def _add_article_action(self):
        LOG.debug('_add_article_action called')
        title = self.title_edit.text()
        path = self._open_file(title)

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

    def _get_article_action(self, title):
        title = title.text()
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

        self.articles_list.clear() # TODO: Add status indicator
        self.article_content_editor.clear()

        title = self.title_edit.text()

        self.worker = Worker(lambda:
                             self._show_articles_list(
                                 self.client.get_titles(), title))
        self.worker.signal_finished.connect(lambda: None)
        self.worker.signal_error.connect(lambda: None)
        self.worker.start()

    def init_client(self, eth_private_key, eth_provider):
        self.client = DWClient(eth_private_key, eth_provider)

    def start(self, app):
        login_window = Login(self.init_client)
        login_window.exec()

        self.show()
        sys.exit(app.exec_())

    def closeEvent(self, QCloseEvent):
        utils.kill_ipfsd_processes()
        # Delete GUI session
        self.deleteLater()
