"""
Uses a file through a copy in a temporary folder that goes away afterwards (p292).

Root cause (r28_insert_check l3, 17.11.2026): importManager.importToTarget of a .f3d wrote a folder _XRef_ with copies
of the part files beside the file it imported, so a box build left files in the add-in's own folder (resources/predBox).
Imported from a copy, whatever Fusion writes lands in the temporary folder and is removed with it. Test:
tests/test_temp_copy.py
"""

import os
import shutil
import tempfile


def withTempCopy(path: str, use):
    """use(copy) with a copy of the file under the same name in a fresh temporary folder; returns what use returns"""
    folder = tempfile.mkdtemp(prefix='gridkeeper-')
    try:
        copy = os.path.join(folder, os.path.basename(path))
        shutil.copyfile(path, copy)
        return use(copy)
    finally:
        # a copy Fusion still holds stays behind; the prefix gridkeeper- makes such a folder easy to find in %TEMP%
        shutil.rmtree(folder, ignore_errors=True)
