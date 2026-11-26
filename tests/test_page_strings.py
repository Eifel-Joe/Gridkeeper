"""
The pages replace their English texts with the ones the dialog sends (lib/ui/html/fusionBridge.js, round 60). Runs
the bridge in node against a small stand-in of the page, skipped without node.
"""

import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "lib", "ui", "html", "fusionBridge.js")
NODE = shutil.which("node")

HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
function element(attributes, text) {
    return { attributes, textContent: text, title: attributes['title'] || '', placeholder: '',
             getAttribute(name) { return this.attributes[name]; } };
}
const heading = element({'data-i18n': 'Compartments'}, 'Compartments');
const button = element({'data-i18n-title': 'Merge the cells', 'title': 'Merge the cells'}, '+');
const field = element({'data-i18n-placeholder': 'Label text'}, '');
const other = element({'data-i18n': 'Not translated'}, 'Not translated');
const all = [heading, button, field, other];
const document = {
    head: { appendChild() {} },
    fonts: { ready: Promise.resolve() },
    querySelectorAll(selector) {
        const name = selector.slice(1, -1);
        return all.filter((e) => name in e.attributes);
    },
};
const context = { document, window: { addEventListener() {} }, setTimeout, Promise, JSON, console };
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8') + '\nthis.fusionBridge = fusionBridge;', context);
const bridge = context.fusionBridge;
const before = bridge.t('Depth {depth} mm', {depth: '3'});
const data = bridge.receiveForTest(JSON.stringify({ fontUrl: '', data: {x: 1}, strings: {
    'Compartments': 'Fächer', 'Merge the cells': 'Zellen zusammenfassen', 'Label text': 'Beschriftung',
    'Depth {depth} mm': 'Tiefe {depth} mm' } }));
console.log(JSON.stringify({
    data, before,
    after: bridge.t('Depth {depth} mm', {depth: '3,5'}),
    missing: bridge.t('Reset'),
    heading: heading.textContent, title: button.title, placeholder: field.placeholder, other: other.textContent,
}));
"""


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_the_bridge_puts_in_the_strings(tmp_path):
    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS, encoding="utf-8")
    result = subprocess.run([NODE, str(harness), BRIDGE], capture_output=True, text=True, encoding="utf-8", check=True)
    output = json.loads(result.stdout)
    assert output["data"] == {"x": 1}
    assert output["before"] == "Depth 3 mm"
    assert output["after"] == "Tiefe 3,5 mm"
    assert output["missing"] == "Reset"
    assert output["heading"] == "Fächer"
    assert output["title"] == "Zellen zusammenfassen"
    assert output["placeholder"] == "Beschriftung"
    assert output["other"] == "Not translated"
