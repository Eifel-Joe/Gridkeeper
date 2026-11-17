# Reload matrix (spec E13), step "update on disk": puts 9.9.9 into the running TEST installation with updateInstall
# (ZIP built from the worktree, no network). The add-in keeps running 9.9.8 until a reload way is applied.
# Run with _runner.py, JOBS = ['uh_m_install'].
import hashlib, io, sys

sys.path.insert(0, r'D:\Entwicklung\Gridfinity\Gridkeeper\.claude\worktrees\upstream-2026-11-16-e588a3\dev-notes\tools\update-fusion-jobs')
import uh_common

TEST_ADDIN = r'D:\Entwicklung\Gridfinity\uh-test\Gridkeeper'


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Release:
    def __init__(self, payload):
        self.version = (9, 9, 9)
        self.assetUrl = 'https://example.invalid/Gridkeeper-v9.9.9.zip'
        self.assetSize = len(payload)
        self.assetDigest = 'sha256:' + hashlib.sha256(payload).hexdigest()


def run(_context):
    updateCheck = uh_common.load('updateCheck')
    updateInstall = uh_common.load('updateInstall')
    print('before', updateCheck.manifestVersion(TEST_ADDIN))
    payload = uh_common.releaseZip('9.9.9')
    way = updateInstall.install(Release(payload), TEST_ADDIN, urlopen=lambda request, timeout=None: Response(payload))
    print('install way:', way, '(renamed = folder moved while Fusion runs it, copied = fallback)')
    print('after', updateCheck.manifestVersion(TEST_ADDIN))
