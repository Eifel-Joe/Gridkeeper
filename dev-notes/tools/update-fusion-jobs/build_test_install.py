# Builds a test installation of Gridkeeper from the worktree as release.yml packs it, for the reload matrix of the
# update round (spec E13): python build_test_install.py <folder> <version>, e.g.
#   python build_test_install.py D:\Entwicklung\Gridfinity\uh-test\Gridkeeper 9.9.8
# The folder is replaced. It has no .git, so the update check treats it like a release installation.
import os
import shutil
import sys

import uh_common

if __name__ == '__main__':
    (folder, version) = sys.argv[1:3]
    if os.path.basename(os.path.normpath(folder)) != 'Gridkeeper':
        sys.exit('the folder must be named Gridkeeper, Fusion loads the add-in only from a folder named like its manifest')
    if os.path.exists(os.path.join(folder, '.git')):
        sys.exit('refusing to replace a git checkout')
    shutil.rmtree(folder, ignore_errors=True)
    uh_common.writeFolder(folder, version, {'commands/commandCreateBin/commandConfig/marker.json': b'{"testInstall": true}'})
    print('built', folder, version)
