from PyQt5.QtCore import QThread, pyqtSignal


class Worker(QThread):
    signal_finished = pyqtSignal()
    signal_error = pyqtSignal(str)

    def __init__(self, fn, *args):
        QThread.__init__(self)

        self.fn = fn
        self.args = args

    def run(self):
        try:
            self.fn(*self.args)
            self.signal_finished.emit()
        except Exception as e:
            self.signal_error.emit(str(e))
