# p321: Gridkeeper reloads itself through Fusion's API (app.scripts, its own Script.stop and run), measured 18.11.2026
# in dev-notes/specs/2026-11-17-update-hinweis-design.md. The Fusion-free decisions of lib/selfReload.py
from lib import selfReload


class FakeScript:
    def __init__(self, folder, name='Gridkeeper', stopResult=True, runResult=True, stopError=None, runError=None):
        self.folder = folder
        self.name = name
        self.stopResult = stopResult
        self.runResult = runResult
        self.stopError = stopError
        self.runError = runError
        self.calls = []

    def stop(self):
        self.calls.append('stop')
        if self.stopError:
            raise self.stopError
        return self.stopResult

    def run(self):
        self.calls.append('run')
        if self.runError:
            raise self.runError
        return self.runResult


def test_reload_offered_only_for_two_known_different_versions():
    assert selfReload.reloadOffered((1, 1, 0), (1, 2, 0))
    # also an older manifest, e.g. after switching to an older branch in a git checkout (spec R4)
    assert selfReload.reloadOffered((1, 2, 0), (1, 1, 0))
    assert not selfReload.reloadOffered((1, 1, 0), (1, 1, 0))
    assert not selfReload.reloadOffered(None, (1, 1, 0))
    assert not selfReload.reloadOffered((1, 1, 0), None)


def test_own_script_by_folder_never_by_name():
    clone = FakeScript('D:/Entwicklung/Gridfinity/Gridkeeper')
    copy = FakeScript('C:/Users/x/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/AddIns/Gridkeeper')
    other = FakeScript('D:/somewhere/Else', name='Else')
    scripts = [other, clone, copy]
    assert selfReload.ownScript(scripts, r'D:\Entwicklung\Gridfinity\Gridkeeper') is clone
    assert selfReload.ownScript(scripts, r'c:\users\x\appdata\roaming\autodesk\autodesk fusion 360\api\addins\gridkeeper\\') is copy


def test_own_script_none_unless_exactly_one():
    assert selfReload.ownScript([], 'D:/a/Gridkeeper') is None
    assert selfReload.ownScript([FakeScript('D:/b/Gridkeeper')], 'D:/a/Gridkeeper') is None
    assert selfReload.ownScript([FakeScript('D:/a/Gridkeeper'), FakeScript('D:/a/Gridkeeper/')], 'D:/a/Gridkeeper') is None
    # Fusion gives an empty folder for some scripts
    assert selfReload.ownScript([FakeScript(''), FakeScript(None)], 'D:/a/Gridkeeper') is None


def test_next_step_waits_while_a_gridkeeper_command_is_open():
    prefix = 'EifelJoe_Gridkeeper_'
    assert selfReload.nextStep('EifelJoe_Gridkeeper_cmdUpdates', prefix, 0, 30) == 'wait'
    assert selfReload.nextStep('EifelJoe_Gridkeeper_cmdBin', prefix, 29, 30) == 'wait'
    assert selfReload.nextStep('EifelJoe_Gridkeeper_cmdBin', prefix, 30, 30) == 'giveUp'
    assert selfReload.nextStep('SelectCommand', prefix, 0, 30) == 'reload'
    assert selfReload.nextStep('', prefix, 5, 30) == 'reload'
    assert selfReload.nextStep(None, prefix, 30, 30) == 'reload'


def test_reload_script_stops_then_runs():
    script = FakeScript('D:/a/Gridkeeper')
    assert selfReload.reloadScript(script) is None
    assert script.calls == ['stop', 'run']


def test_reload_script_not_stopped_keeps_the_old_version():
    for script in (FakeScript('D:/a', stopResult=False), FakeScript('D:/a', stopError=RuntimeError('3 : busy'))):
        result = selfReload.reloadScript(script)
        assert result.stillRunning
        assert script.calls == ['stop']
    assert '3 : busy' in selfReload.reloadScript(FakeScript('D:/a', stopError=RuntimeError('3 : busy'))).reason


def test_reload_script_stopped_but_not_started():
    for script in (FakeScript('D:/a', runResult=False), FakeScript('D:/a', runError=RuntimeError('2 : failed'))):
        result = selfReload.reloadScript(script)
        assert not result.stillRunning
        assert script.calls == ['stop', 'run']
