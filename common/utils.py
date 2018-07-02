import hashlib
import logging
import os
from pathlib import Path

import psutil

LOG = logging.getLogger('utils')


def file_hash(filename):
    h = hashlib.sha256()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda: f.read(128 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def create_file_if_not_exists(path):
    open(path, 'a').close()


def get_prefix_path():
    if os.name == 'nt':
        prefix_path = os.getenv("APPDATA")
        path = os.path.join(prefix_path, "DistributedWiki")
    else:
        username = os.getenv("USER")
        path = os.path.join("/home", username, ".DistributedWiki")

    if not os.path.exists(path):
        os.makedirs(path)

    return path


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
        LOG.debug('Ipfsd lock doesn\'t exists - OK')