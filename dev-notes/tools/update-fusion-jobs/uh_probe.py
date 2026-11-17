# Fusion job 3 of the update round (p310, spec E13 W3): what Fusion's API offers to stop and start add-ins. Only
# reads and prints, starts or stops nothing. Run with _runner.py, JOBS = ['uh_probe'].
import adsk.core


def members(obj):
    return [name for name in dir(obj) if not name.startswith('_')]


def run(_context):
    app = adsk.core.Application.get()
    print('Fusion', app.version)
    candidates = [name for name in dir(app) if any(word in name.lower() for word in ('script', 'addin', 'add_in'))]
    print('Application members with script/addin:', candidates)
    print('adsk.core types with script/addin:', [name for name in dir(adsk.core) if any(word in name.lower() for word in ('script', 'addin'))])
    for name in candidates:
        try:
            value = getattr(app, name)
        except Exception as err:
            print(name, 'error', err)
            continue
        print('---', name, type(value).__name__, members(value))
        count = getattr(value, 'count', None)
        if isinstance(count, int):
            for index in range(count):
                item = value.item(index)
                fields = {}
                for field in ('name', 'id', 'isAddIn', 'isRunning', 'path', 'isRunOnStartup', 'manifestFile'):
                    try:
                        fields[field] = getattr(item, field)
                    except Exception as err:
                        fields[field] = 'n/a'
                if 'ridkeeper' in str(fields) or index < 3:
                    print(index, fields)
            if count:
                print('item members:', members(value.item(0)))
