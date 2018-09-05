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
            gc.FHD_W / 2 - gc.FRAME_WIDTH / 2, gc.FHD_H / 2 - gc.FRAME_HEIGHT / 2
        )
        self.setWindowTitle(gc.WINDOW_TITLE)

        self.client = None
        self._constructUI()
        self.worker = None
        self.article_version_history = None

        os.chdir(utils.get_prefix_path())

    def update_titles(self, _):
        self.worker = Worker(lambda:
                             self.titles_list_model.setStringList(
                                 self.client.get_titles()))
        self.worker.signal_finished.connect(lambda: None)
        self.worker.signal_error.connect(lambda: None)
        self.worker.start()

    def _set_estimated_price(self, price):
        text = "estimated tx price: " + str(price) + " wei"
        self.estimated_tx_price.setText(text)

    def _update_estimation_price(self):
        self.worker = Worker(lambda: self.client.estimate_transaction_cost())
        self.worker.signal_finished.connect(
            lambda:
            self._set_estimated_price(
                self.client.estimate_transaction_cost())) # This call should be getting cached value.
        self.worker.signal_error.connect(lambda: None)
        self.worker.start()

    def _constructUI(self):
        status_title = QLabel("FullNode:", self)
        status_title.move(50, 25)

        status_variable = QLabel("active", self)
        status_variable.setStyleSheet("QLabel {color: green;}")
        status_variable.move(100, 25)

        self.estimated_tx_price = QLabel("estimated tx price: 99999999999 wei", self)
        self.estimated_tx_price.move(135, 25)
        self.estimated_tx_price.setToolTip("Click to refresh value")
        self.estimated_tx_price.mousePressEvent = lambda _: self._update_estimation_price()

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
        self._set_estimated_price(self.client.get_last_transaction_cost())

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

    def _set_current_article_title(self, title):
        self.article_title_label.setText("Current article: {}".format(title))

    def _show_warning_box(self, warning):
        box = QMessageBox()
        box.setIcon(QMessageBox.Warning)
        box.setText(warning)
        box.setWindowTitle("Warning")
        box.exec()

    def _add_article_action_success(self, title):
        self._set_current_article_title(title)
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._set_estimated_price(self.client.get_last_transaction_cost())

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

    def _search_article_action_success(self, title):
        self._set_current_article_title(title)
        self.client.initialize_article_data(title)
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self.client.get_versions_list()
        )
        self._open_file(title)

    def _search_article_action(self):
        LOG.debug('_search_article_action called')
        title = self.title_edit.text()

        self.worker = Worker(self.client.get_article, title)
        self.worker.signal_finished.connect(
            lambda: self._search_article_action_success(title)
        )
        self.worker.signal_error.connect(self._client_action_failed)
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
