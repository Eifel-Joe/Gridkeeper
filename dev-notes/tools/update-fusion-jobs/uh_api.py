# Fusion job 1 of the update round (p310, plan Task 6): Fusion's own Python asks the real GitHub API (SSL works?),
# finds gridkeeper-v1.0.0, downloads its real ZIP and checks it against GitHub's digest. Only reads from GitHub, writes
# to fusion-auftraege\uh_work. Run with _runner.py, JOBS = ['uh_api'].
import hashlib, os, ssl, sys, time

sys.path.insert(0, r'D:\Entwicklung\Gridfinity\Gridkeeper\.claude\worktrees\upstream-2026-11-16-e588a3\dev-notes\tools\update-fusion-jobs')
import uh_common

WORK = r'D:\Entwicklung\Gridfinity\fusion-auftraege\uh_work'


def run(_context):
    updateCheck = uh_common.load('updateCheck')
    updateInstall = uh_common.load('updateInstall')
    print('python', sys.version.split()[0], ssl.OPENSSL_VERSION)
    started = time.time()
    logs = []
    releases = updateCheck.fetchReleases(log=logs.append)
    print('fetch %.1f s' % (time.time() - started), 'releases', None if releases is None else len(releases), 'logs', logs)
    if releases is None:
        return
    print('tags', [entry.get('tag_name') for entry in releases])
    newest = updateCheck.newestRelease(releases, (0, 9, 0))
    print('newest vs 0.9.0:', newest)
    print('newest vs 1.0.0:', updateCheck.newestRelease(releases, (1, 0, 0)))
    print('summary:', repr(newest.summary))
    os.makedirs(WORK, exist_ok=True)
    target = os.path.join(WORK, 'Gridkeeper-v%s.zip' % newest.versionText)
    started = time.time()
    updateInstall.download(newest.assetUrl, target)
    print('download %.1f s' % (time.time() - started), os.path.getsize(target), 'bytes, asset size', newest.assetSize)
    updateInstall.verifyZip(target, newest.version, newest.assetDigest, newest.assetSize)
    print('verifyZip OK, digest', newest.assetDigest)
    os.remove(target)
