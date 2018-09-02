from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal


class BackgroundWorker(QThread):
    job_done_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, job, job_done, error, run_in_loop=False):
        """
        :param job: function to be called in worker thread
        :param job_done: callback function to be called in caller's thread.
            Should be function taking one parameter (result from job)
        :param error: callback function to be called in caller's thread
            in case of an exception
        :param run_in_loop: flag specifying whether to job should be called once
            or in a loop
        """
        QThread.__init__(self)

        self.job = job
        self.job_done_signal.connect(job_done)
        self.error_signal.connect(error)
        self.run_in_loop = run_in_loop

    def run(self):
        self._run_job()

        if self.run_in_loop:
            while True:
                sleep(1)
                self._run_job()

    def _run_job(self):
        try:
            result = self.job()
            self.job_done_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
