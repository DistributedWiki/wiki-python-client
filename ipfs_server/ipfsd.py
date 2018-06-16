import io
import logging
import os
import subprocess
from threading import Thread
from zipfile import ZipFile

import requests

import ipfs_server.ipfsd_conf as cfg

LOG = logging.getLogger('ipfsd')


class Ipfsd(Thread):
    """
    IPFS Daemon lifecycle controller
    """
    def __init__(self):
        super().__init__()
        self.version = cfg.VERSION
        # TODO(pkobielak): manual selection or automatic resolving of platform?
        self.platform = cfg.PLATFORM_WIN64

        if self._is_installed():
            self.exe = self._get_default_exe_path()
            LOG.info('IPFS daemon is already installed')
        else:
            self.exe = self._download_and_extract()

    def _is_installed(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.isdir(os.path.join(self.current_dir, 'tmp', 'go-ipfs'))

    def _get_default_exe_path(self):
        # TODO(pkobielak): 'ipfs.exe' should be variable and platform specific
        return os.path.join(self.current_dir, 'tmp', 'go-ipfs', 'ipfs.exe')

    def _download_and_extract(self):
        LOG.info('Downloading ipfs daemon package...')
        # TODO(pkobielak): add more platforms to work with
        workdir = ''
        if self.platform == cfg.PLATFORM_WIN64:
            pkg_name = '_'.join([
                'go-ipfs', cfg.VERSION, cfg.PLATFORM_WIN64
            ])
            pkg_name = '.'.join([pkg_name, 'zip'])
            url = '/'.join([cfg.DIST_URL, cfg.VERSION, pkg_name])

            # TODO(pkobielak): we should check for errors here
            pkg = requests.get(url).content

            workdir = os.path.join(self.current_dir, 'tmp')
            os.mkdir(workdir)

            zf = ZipFile(io.BytesIO(pkg))
            zf.extractall(workdir)
        else:
            LOG.fatal('Platform not supported!')

        LOG.info('Downloaded and extracted ipfs daemon %s', cfg.VERSION)
        return os.path.join(workdir, 'go-ipfs', 'ipfs.exe')

    def run(self):
        LOG.info('Attempting to run IPFS daemon...')
        if self.exe is not None:
            subprocess.call([self.exe, 'init'])
            subprocess.call([self.exe, 'daemon'])
