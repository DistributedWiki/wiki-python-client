from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal


class BackgroundWorker(QThread):
    job_done = pyqtSignal(object)
    error = pyqtSignal(object)

    def __init__(self, job, job_done_slot, error_slot):
        QThread.__init__(self)

        self.job = job
        self.job_done.connect(job_done_slot)
        self.error.connect(error_slot)

    def run(self):
        while True:
            try:
                result = self.job()
                self.job_done.emit(result)
            except Exception as e:
                self.error.emit(e)

            sleep(1)

