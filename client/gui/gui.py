import logging
import os
import subprocess
import sys

from PyQt5 import QtGui
from PyQt5.Qt import QSize
from PyQt5.QtWidgets import QTableWidget, QMessageBox
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QHeaderView
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
from client.gui.background_worker import BackgroundWorker
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
            gc.FHD_W / 2 - gc.FRAME_WIDTH / 2,
            gc.FHD_H / 2 - gc.FRAME_HEIGHT / 2
        )
        self.setWindowTitle(gc.WINDOW_TITLE)

        self._constructUI()

        self.client = None
        self.article_version_history = None

        os.chdir(utils.get_prefix_path())

        self.tx_monitor = BackgroundWorker(
            job=self._get_actions,
            job_done=self._process_actions,
            error=self._actions_fetch_failed,
            run_in_loop=True)

        self.warmup_worker = None
        self.worker_update = None
        self.worker_add = None
        self.worker_search = None
        self.worker_get = None

        self.loading_box = None

    def _constructUI(self):
        self.top_level = QLabel(
            "Current top level address: " + DEV_TOP_LEVEL_ADDRESS, self
        )

        self.top_level.resize(QSize(400, 25))
        self.top_level.move(50, 20)

        self.estimated_tx_price = QLabel("estimated tx price: loading...", self)
        self.estimated_tx_price.adjustSize()
        self.estimated_tx_price.move(550, 505)
        self.estimated_tx_price.setToolTip("Click to refresh value")
        self.estimated_tx_price.mousePressEvent = \
            lambda _: self._update_estimation_price()

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

        self.btn_add_article = QPushButton('Add article', self)
        self.btn_add_article.resize(QSize(90, 25))
        self.btn_add_article.move(410, 50)
        self.btn_add_article.clicked.connect(self._add_article_action)

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

        action_status_label = QLabel(
            "Last " + str(gc.NUMBER_OF_DISPLAYED_TRANSACTIONS) +
            " blockchain actions", self)

        action_status_label.adjustSize()
        action_status_label.move(50, 505)

        self.action_status = QTableWidget(self)
        self.action_status.resize(QSize(710, 175))
        self.action_status.move(50, 530)
        self.action_status.setColumnCount(2)
        self.action_status.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Fixed)
        self.action_status.setHorizontalHeaderLabels(['Action', 'Status'])
        self.action_status.setColumnWidth(0, 473)
        self.action_status.setColumnWidth(1, 220)

        self.statusBar().showMessage('Connected')

    def _show_articles_list(self, articles, prefix):
        count = 0
        self.articles_list.setDisabled(False)

        for article in articles:
            if prefix in article:
                self.articles_list.addItem(article)
                count += 1

        if count == 0:
            self.articles_list.addItem("No articles found")
            self.articles_list.setDisabled(True)

        self.articles_list.show()

    def _set_estimated_price(self, price):
        text = "estimated tx price: {0:.3f} gwei".format(price / 10**9)
        self.estimated_tx_price.setText(text)
        self.estimated_tx_price.adjustSize()

    def _add_action(self, action, status):
        row = self.action_status.rowCount()
        self.action_status.insertRow(row)

        self.action_status.setItem(row, 0, QTableWidgetItem(action))
        self.action_status.setItem(row, 1, QTableWidgetItem(status))

        if status == 'failed':
            self.action_status.item(row, 1).\
                setBackground(QtGui.QColor(200, 0, 0))
        elif status == 'success':
            self.action_status.item(row, 1).\
                setBackground(QtGui.QColor(0, 200, 0))

    def _get_actions(self):
        return self.client.get_unprocessed_tx(
            gc.NUMBER_OF_DISPLAYED_TRANSACTIONS)

    def _actions_fetch_failed(self, cause):
        self.action_status.clear()
        self.action_status.setHorizontalHeaderLabels(['Action', 'Status'])
        self._add_action(
            "Failed to fetch transactions, check your connection", cause)
        self.action_status.setRowCount(gc.NUMBER_OF_DISPLAYED_TRANSACTIONS)

    def _process_actions(self, action_list):
        self.action_status.clear()
        self.action_status.setHorizontalHeaderLabels(['Action', 'Status'])
        for action in action_list:
            self._add_action(action['description'], action['status'])

        self.action_status.sortItems(0)
        self.action_status.sortItems(1)

        self.action_status.setRowCount(gc.NUMBER_OF_DISPLAYED_TRANSACTIONS)

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
        self._close_loading()
        self._set_app_status('Error occurred: {}'.format(cause))

    def _update_article_action(self):
        LOG.info('_update_article_action called')
        self._set_app_status('Updating article...')

        title = self.title_edit.text()

        # update button should only be active when title is specified
        assert(title is not None)
        assert(title != "")

        path = self._open_file(title)

        self._set_app_status(
            'Synchronizing article with distributed systems...'
        )

        self.worker_update = BackgroundWorker(
            job=lambda: self.client.update_article(title, path),
            job_done=lambda result: self._close_loading(),
            error=self._client_action_failed
        )
        self.worker_update.start()

        self._show_loading("Updating article on IPFS")

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

    def _show_loading(self, message):
        self.loading_box = QMessageBox()
        self.loading_box.setIcon(QMessageBox.Information)
        self.loading_box.setStandardButtons(QMessageBox.Close)
        self.loading_box.button(QMessageBox.Close).setDisabled(True)
        self.loading_box.setText(message)
        self.loading_box.setWindowTitle("Warning")
        self.loading_box.exec()

    def _close_loading(self):
        if self.loading_box is not None:
            self.loading_box.close()
        self.loading_box = None

    def _add_article_action_open_and_push(self, title):
        path = self._open_file(title)

        self.worker_add = BackgroundWorker(
            job=lambda: self.client.add_article(title, path),
            job_done=lambda result: self._close_loading(),
            error=self._client_action_failed
        )
        self.worker_add.start()

        self._set_app_status(
            'Synchronizing article with distributed systems...'
        )

        self._show_loading("Adding article to IPFS")

    def _add_article_action(self):
        LOG.debug('_add_article_action called')
        self._set_app_status('Adding an article...')
        title = self.title_edit.text()

        if title == "":
            self._client_action_failed("Article name must not be empty")
            return

        self.worker_add = BackgroundWorker(
            job=lambda: self.client.article_exists(title),
            job_done=lambda result:
                self._add_article_action_open_and_push(title) if result == 0
                else self._client_action_failed("Article already exists"),
            error=self._client_action_failed
        )
        self.worker_add.start()

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

        self.worker_get = BackgroundWorker(
            job=lambda: self.client.get_article(title),
            job_done=lambda result: self._get_article_action_success(title),
            error=self._client_action_failed
        )
        self.worker_get.start()

    def _search_article_action_success(self, articles, title):
        self._show_articles_list(articles, title)
        self._set_app_status('Listed found articles')

    def _search_article_action(self):
        LOG.debug('_search_article_action called')
        self._set_app_status('Searching for an article...')
        self.articles_list.clear()
        self.article_content_editor.clear()

        title = self.title_edit.text()

        self.worker_search = BackgroundWorker(
            job=lambda: self.client.get_titles(),
            job_done=lambda result: self._search_article_action_success(
                result, title),
            error=self._client_action_failed)
        self.worker_search.start()

    def init_client(self, eth_private_key, eth_provider, top_level_address):
        self._set_app_status('Initializing client...')
        self.client = DWClient(eth_private_key, eth_provider, top_level_address)
        self._set_app_status('Client initialized')
        self.tx_monitor.start()

        self.warmup_worker = BackgroundWorker(
            job=self.client.get_transaction_price,
            job_done=lambda result:  self._set_estimated_price(result),
            error=lambda error: None
        )
        self.warmup_worker.start()

    def start(self, app):
        login_window = Login(self.init_client)
        result = login_window.exec()

        if result == 0:
            self.close()
            sys.exit(0)

        self.show()
        sys.exit(app.exec_())

    def closeEvent(self, QCloseEvent):
        self._set_app_status('Closing application...')
        utils.kill_ipfsd_processes()
        # Delete GUI session
        self.deleteLater()
