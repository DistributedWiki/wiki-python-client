import logging
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from time import sleep

from PyQt5.Qt import QSize
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QListWidget

import client.gui.gui_conf as gc
import common.utils as utils
from client.client import DWClient
from client.gui.Worker import Worker

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

        self._constructUI()
        self.client = DWClient()

        os.chdir(utils.get_prefix_path())

    def _constructUI(self):
        status_title = QLabel("FullNode:", self)
        status_title.move(50, 25)

        status_variable = QLabel("active", self)
        status_variable.setStyleSheet("QLabel {color: green;}")
        status_variable.move(100, 25)

        self.title_edit = QTextEdit(
            self,
            placeholderText='Put unique article title here'
        )
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

    def _show_clicked_article_version(self):
        LOG.info('_show_clicked_article_version')
        LOG.fatal('_show_clicked_article_version is not implemented')

    def _client_action_failed(self, cause):
        self._show_warning_box(cause)
        self._set_current_article_title("<none>")

    def _update_article_action_success(self, title):
        self.version_history_list.clear()
        self.version_history_list.addItems(
            self._make_versions_list(title)
        )

    def _update_article_action(self):
        LOG.info('_update_article_action called')
        title = self.title_edit.toPlainText()
        path = self._open_file(title)

        self.worker = Worker(self.client.update_article, title, path)
        self.worker.signal_finished.connect(lambda: self._update_article_action_success(title))
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

        self.version_history_list.clear()
        self.version_history_list.addItems(
            self._make_versions_list(title)
        )

    def _add_article_action(self):
        LOG.debug('_add_article_action called')
        title = self.title_edit.toPlainText()
        path = self._open_file(title)

        self.worker = Worker(self.client.add_article, title, path)
        self.worker.signal_finished.connect(lambda: self._add_article_action_success(title))
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def _make_versions_list(self, title):
        """
        Makes list of strings for QListWidget.
        :param title: title of the article
        :return: list of strings
        """
        versions_data = self.client.get_article_history(title)
        history_list = []
        for version_dict in versions_data:
            history_list.append("Time: {}".format(version_dict['timestamp']))
        return history_list

    def _search_article_action_success(self, title):
        self._set_current_article_title(title)

        self.version_history_list.clear()
        self.version_history_list.addItems(
            self._make_versions_list(title)
        )
        self._open_file(title)

    def _search_article_action(self):
        LOG.debug('_search_article_action called')
        title = self.title_edit.toPlainText()

        self.worker = Worker(self.client.get_article, title)
        self.worker.signal_finished.connect(lambda: self._search_article_action_success(title))
        self.worker.signal_error.connect(self._client_action_failed)
        self.worker.start()

    def start(self, app):
        self.show()
        sys.exit(app.exec_())

    def closeEvent(self, QCloseEvent):
        utils.kill_ipfsd_processes()
        # Delete GUI session
        self.deleteLater()
