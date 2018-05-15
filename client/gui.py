import logging
import sys

from PyQt5.Qt import QSize
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget

import client.gui_conf as gc
from client.client import DWClient

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

    def _constructUI(self):
        btn_add_article = QPushButton('Add article...', self)
        btn_add_article.resize(btn_add_article.sizeHint())
        btn_add_article.move(50, 50)
        btn_add_article.clicked.connect(self._add_article_action)

        self.lbl_article_path = QLabel('<article_filepath>', self)
        self.lbl_article_path.resize(QSize(700, 15))
        self.lbl_article_path.move(50, 80)

    def _add_article_action(self):
        LOG.debug('_add_article_action called')
        article_filepath = QFileDialog.getOpenFileName()[0]
        LOG.debug('Received article_filepath = %s', article_filepath)
        self.lbl_article_path.setText(article_filepath)
        LOG.debug('_add_article_action calls client.add_article')
        self.client.add_article(article_filepath)

    def start(self, app):
        self.show()
        sys.exit(app.exec_())
