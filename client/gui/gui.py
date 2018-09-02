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
from PyQt5.QtWidgets import QMainWindow

import client.gui.gui_conf as gc
import common.utils as utils
from client.client import DWClient
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

    def update_titles(self, _):
        self._set_app_status('Loading suggestions for title')
        self.worker = Worker(lambda:
                             self.titles_list_model.setStringList(
                                 self.client.get_titles()))
        self.worker.signal_finished.connect(lambda:
                                            self._set_app_status(
                                                'Suggestions loaded'
                                            ))
        self.worker.signal_error.connect(lambda:
                                         self._set_app_status(
                                             'Failed to load suggestions'
                                         ))
        self.worker.start()

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

        self.titles_list_model = QStringListModel()
        self.title_edit.textChanged.connect(self.update_titles)

        completer = QCompleter()
        completer.setModel(self.titles_list_model)
        self.title_edit.setCompleter(completer)

        self.title_edit.resize(QSize(250, 25))
        self.title_edit.move(50, 50)

        self.article_title_label = QLabel("Current article: <none>", self)
        self.article_title_label.resize(QSize(250, 20))
        self.article_title_label.move(50, 75)

        btn_add_article = QPushButton('Add article', self)
        btn_add_article.resize(btn_add_article.sizeHint())
        btn_add_article.move(50, 100)
        btn_add_article.clicked.connect(self._add_article_action)

        btn_update_article = QPushButton('Update article', self)
        btn_update_article.resize(btn_update_article.sizeHint())
        btn_update_article.move(138, 100)
        btn_update_article.clicked.connect(self._update_article_action)

        btn_search_article = QPushButton('Search article', self)
        btn_search_article.resize(btn_search_article.sizeHint())
        btn_search_article.move(225, 100)
        btn_search_article.clicked.connect(self._search_article_action)

        version_history_label = QLabel("Version history", self)
        version_history_label.move(50, 150)

        self.version_history_list = QListWidget(self)
        self.version_history_list.resize(QSize(250, 200))
        self.version_history_list.move(50, 170)
        self.version_history_list.itemClicked.connect(
            self._show_clicked_article_version
        )

        self.article_content_editor = QPlainTextEdit(self, readOnly=True)
        self.article_content_editor.resize(QSize(350, 345))
        self.article_content_editor.move(325, 25)

        self.statusBar().showMessage('Connected')

    def _set_app_status(self, text):
        self.statusBar().showMessage(
            'Status: Connected | Last action: {}'.format(text)
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

    def _set_current_article_title(self, title):
        self.article_title_label.setText("Current article: {}".format(title))

    def _add_article_action_success(self, title):
        self._set_current_article_title(title)
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

        self.worker = Worker(self.client.add_article, title, path)
        self.worker.signal_finished.connect(
            lambda: self._add_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def _search_article_action_success(self, title):
        self._set_current_article_title(title)
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._open_file(title)
        self._set_app_status('Article found')

    def _search_article_action(self):
        LOG.debug('_search_article_action called')
        self._set_app_status('Searching for an article...')
        title = self.title_edit.text()

        self.worker = Worker(self.client.get_article, title)
        self.worker.signal_finished.connect(
            lambda: self._search_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def init_client(self, eth_private_key, eth_provider):
        self._set_app_status('Initializing client...')
        self.client = DWClient(eth_private_key, eth_provider)
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
