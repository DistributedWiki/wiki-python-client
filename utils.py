import logging
from pathlib import Path
import psutil
import os

LOG = logging.getLogger('utils')


def kill_ipfsd_processes():
    for proc in psutil.process_iter(attrs=['name']):
        if 'ipfs.exe' == proc.info['name']:
            LOG.debug('Ipfs daemon found with pid %s', proc.pid)
            proc.kill()
            LOG.debug('Killed process with pid: %s', proc.pid)


def remove_local_ipfs_lock():
    LOG.info('Removing ipfsd lock...')
    home = str(Path.home())
    lock_path = os.path.join(home, '.ipfs', 'repo.lock')
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        LOG.debug('Ipfsd lock not exists - OK')
