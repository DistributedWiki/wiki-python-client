import logging
import sys

from PyQt5.QtWidgets import QApplication

from client.gui import GUI
from ipfs_server.ipfsd import Ipfsd

logging.basicConfig(level=logging.DEBUG)

LOG = logging.getLogger('launch')

LOG.info('Starting local IPFS Daemon...')
local_ipfsd = Ipfsd()
local_ipfsd.start()

LOG.info('Creating application and UI...')
qt_app = QApplication(sys.argv)
gui = GUI()
LOG.info('Starting application...')
gui.start(app=qt_app)
