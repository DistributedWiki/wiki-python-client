import logging
import sys

from PyQt5.QtWidgets import QApplication

import utils
from client.gui import GUI
from ipfs_server.ipfsd import Ipfsd

logging.basicConfig(level=logging.DEBUG)

LOG = logging.getLogger('launch')

LOG.info('Cleaning all running ipfs daemons...')
utils.kill_ipfsd_processes()
utils.remove_local_ipfs_lock()
LOG.info('Starting local IPFS Daemon...')
local_ipfsd = Ipfsd()
local_ipfsd.start()

LOG.info('Creating application and UI...')
qt_app = QApplication(sys.argv)
gui = GUI()
LOG.info('Starting application...')
gui.start(app=qt_app)
