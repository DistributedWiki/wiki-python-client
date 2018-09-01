from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit

import client.gui.gui_conf as gc
from client.client_conf import DEV_INFURA, DEV_PRIVATE_KEY


class Login(QtWidgets.QDialog):
    def __init__(self, callback):
        super(Login, self).__init__(None)

        self.callback = callback

        self.resize(gc.LOGIN_WINDOW_WIDTH, gc.LOGIN_WINDOW_HEIGHT)

        self.private_key_label = QLabel("Enter private key", self)
        self.private_key_label.move(5, 5)

        self.private_key = QtWidgets.QLineEdit(self)
        self.private_key.setEchoMode(QLineEdit.Password)
        self.private_key.move(self.private_key_label.size().width(), 0)
        self.private_key.resize(475, 23)
        self.private_key.setText(
            DEV_PRIVATE_KEY
        )

        self.provider_label = QLabel("Enter provider", self)
        self.provider_label.move(5, 30)

        self.provider = QtWidgets.QLineEdit(self)
        self.provider.resize(475, 23)
        self.provider.move(self.provider_label.size().width(), 25)
        self.provider.setText(DEV_INFURA)

        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handle_login)
        self.buttonLogin.move(300 - self.buttonLogin.size().width() / 2, 60)

    def handle_login(self):
        self.callback(self.private_key.text(), self.provider.text())
        self.accept()
