from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMessageBox
import client.gui.gui_conf as gc
from blockchain.blockchain_db import BlockchainDB

MARGIN = 10


class AddAuthorized(QMainWindow):
    """
    This class represents window, to manage access rights.
    User can add specified accounts to a list, which will be passed to
    a smart contract.
    """
    def __init__(self, on_exit):
        super(AddAuthorized, self).__init__()
        self.on_exit = on_exit
        self.address_list = []

        self.resize(gc.ADD_AUTHORIZED_WIDTH, gc.ADD_AUTHORIZED_HEIGHT)

        self.address = QLineEdit(self)
        self.address.resize(QSize(300, 30))
        self.address.move(MARGIN, 0)

        self.add = QPushButton(self)
        self.add.resize(QSize(self.add.width(), 30))
        self.add.setText("Add")
        self.add.clicked.connect(self.add_address)
        self.add.move(self.address.width() + 2 * MARGIN, 0)

        self.list = QListWidget(self)
        self.list.resize(QSize(
            self.address.width() + self.add.width() + MARGIN, 100))
        self.list.move(MARGIN, self.add.height() + MARGIN)

        self.checkbox = QCheckBox(self)
        self.checkbox.move(MARGIN, self.list.pos().y() + self.list.height())
        self.checkbox.setChecked(True)

        self.include_me = QLabel(self)
        self.include_me.setText("Include me")
        self.include_me.move(self.checkbox.pos().x() + 2 * MARGIN,
                             self.checkbox.pos().y())

        self.ok = QPushButton(self)
        self.ok.setText("OK")
        self.ok.clicked.connect(self.exit)
        self.ok.move(self.width() / 2 - self.ok.width() / 2, self.address.height() + self.list.height() + 3 * MARGIN)

    def add_address(self):
        address = self.address.text().strip()
        if BlockchainDB.is_address_valid(address):
            self.list.addItem(address)
            self.address_list.append(address)
        else:
            self.warning_box = QMessageBox()
            self.warning_box.setIcon(QMessageBox.Warning)
            self.warning_box.setStandardButtons(QMessageBox.Ok)
            self.warning_box.setText("Address is ill-formed")
            self.warning_box.setWindowTitle("Invalid address")
            self.warning_box.exec()

    def exit(self):
        self.close()
        self.on_exit(self.address_list, self.checkbox.isChecked())
