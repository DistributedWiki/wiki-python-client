import hashlib
import os


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
