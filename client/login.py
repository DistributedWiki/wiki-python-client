from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLabel

import client.gui.gui_conf as gc


class Login(QtWidgets.QDialog):
    def __init__(self, callback):
        super(Login, self).__init__(None)

        self.callback = callback

        self.resize(gc.LOGIN_WINDOW_WIDTH, gc.LOGIN_WINDOW_HEIGHT)

        self.private_key_label = QLabel("Enter private key", self)
        self.private_key_label.move(5, 5)

        self.private_key = QtWidgets.QLineEdit(self)
        #self.textPass.setEchoMode(QLineEdit.Password) TODO: should it be treated as password?
        self.private_key.move(self.private_key_label.size().width(), 0)
        self.private_key.resize(475, 23)
        self.private_key.setText(
            "fa9bb03a928082551c83892a315850fe659dafd726aa61f40286ec09fac725a7"
        )

        self.provider_label = QLabel("Enter provider", self)
        self.provider_label.move(5, 30)

        self.provider = QtWidgets.QLineEdit(self)
        self.provider.resize(475, 23)
        self.provider.move(self.provider_label.size().width(), 25)
        self.provider.setText("https://ropsten.infura.io/OQe96S6X8l5PM7NexvCM")

        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handle_login)
        self.buttonLogin.move(300 - self.buttonLogin.size().width() / 2, 60)

    def handle_login(self):
        self.callback(self.private_key.text(), self.provider.text())
        self.accept()
