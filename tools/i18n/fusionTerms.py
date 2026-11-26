"""
How German Fusion says an English term, from the string tables of the local Fusion install
(webdeploy/production/<build>/StringTable/de-DE/*.xml: each entry has the English devLabel and the German translation).

Usage: python tools/i18n/fusionTerms.py "Change Parameters" "Joint Origin" ...
       python tools/i18n/fusionTerms.py --table <StringTable/de-DE folder> TERM ...
Prints each term with its most frequent translations, '-' when Fusion doesn't have it. Windows only, where Fusion
installs to %LOCALAPPDATA%/Autodesk/webdeploy/production.
"""

import collections
import glob
import os
import sys
import xml.etree.ElementTree as ElementTree


def findTable() -> str | None:
    """The de-DE string table of the newest Fusion build"""
    pattern = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Autodesk', 'webdeploy', 'production', '*', 'StringTable', 'de-DE')
    folders = sorted(glob.glob(pattern), key=os.path.getmtime)
    return folders[-1] if folders else None


def readTable(folder: str) -> dict[str, collections.Counter]:
    table = collections.defaultdict(collections.Counter)
    for name in os.listdir(folder):
        try:
            root = ElementTree.parse(os.path.join(folder, name)).getroot()
        except (ElementTree.ParseError, OSError):
            continue
        for element in root.iter():
            (english, german) = (element.get('devLabel'), element.get('translation'))
            if english and german:
                table[english.strip()][german.strip()] += 1
    return table


def main(arguments: list[str]) -> int:
    folder = None
    if arguments[:1] == ['--table']:
        (folder, arguments) = (arguments[1], arguments[2:])
    folder = folder or findTable()
    if folder is None:
        print('No Fusion string table found, pass --table', file=sys.stderr)
        return 1
    table = readTable(folder)
    lowered = {english.lower(): english for english in table}
    for term in arguments:
        english = term if term in table else lowered.get(term.lower())
        found = ' | '.join(f'{german} ({count})' for (german, count) in table[english].most_common(3)) if english else '-'
        print(f'{term} => {found}')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main(sys.argv[1:]))
