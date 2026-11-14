"""
Tests for the Cullenect symbol catalog: the building blocks of the rendered screw symbols, the file names
and the lookup of what is on disk.
"""

import os
import importlib.util

from pytest import approx


def _load():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "lib", "gridfinityUtils", "cullenectCatalog.py")
    spec = importlib.util.spec_from_file_location("cullenectCatalog", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


catalog = _load()


def test_screw_combination_count():
    # none head: 4 shaft/thread variants; countersunk: no flange; the rest (3 heads) with flange
    assert len(catalog.allScrewCombinations()) == 480


def test_combinations_are_unique_and_valid():
    combinations = catalog.allScrewCombinations()
    assert len(set(combinations)) == len(combinations)
    assert all(catalog.isValidScrew(*combination) for combination in combinations)


def test_flange_invalid_for_countersunk_and_none():
    assert catalog.isValidScrew('countersunk', 'machine', 'full', 'hex', True, False) is False
    assert catalog.isValidScrew('none', 'machine', 'full', 'none', True, False) is False
    assert catalog.isValidScrew('socket', 'machine', 'full', 'hex', True, False) is True


def test_driver_needs_a_head():
    assert catalog.isValidScrew('none', 'machine', 'full', 'hex', False, False) is False
    assert catalog.isValidScrew('none', 'machine', 'full', 'none', False, False) is True


def test_security_pin_needs_a_driver():
    assert catalog.isValidScrew('socket', 'machine', 'full', 'none', False, True) is False
    assert catalog.isValidScrew('socket', 'machine', 'full', 'torx', False, True) is True


def test_unknown_values_are_invalid():
    assert catalog.isValidScrew('bogus', 'machine', 'full', 'none', False, False) is False
    assert catalog.isValidScrew('socket', 'bogus', 'full', 'none', False, False) is False


def test_file_name():
    assert catalog.screwIconFileName('socket', 'machine', 'full', 'hex', False, False) == 'screw_socket_machine_full_hex_noflange_nosec.svg'
    assert catalog.screwIconFileName('pan', 'tapping', 'partial', 'phillips_slot', True, True) == 'screw_pan_tapping_partial_phillips_slot_flange_sec.svg'


def test_hardware_list_and_icon_types():
    assert len(catalog.CULLENECT_HARDWARE) == 18
    assert len(set(catalog.CULLENECT_HARDWARE)) == 18
    assert all(key in catalog.HARDWARE_LABEL_ICON_TYPE for key in catalog.CULLENECT_HARDWARE)
    assert catalog.HARDWARE_LABEL_ICON_TYPE['washer_locking'] == 'washers'
    assert catalog.HARDWARE_LABEL_ICON_TYPE['tnut_2'] == 'nuts'
    assert catalog.HARDWARE_LABEL_ICON_TYPE['nut_nylon'] == 'nuts'
    assert catalog.HARDWARE_LABEL_ICON_TYPE['threaded_insert'] == 'inserts'
    assert catalog.HARDWARE_LABEL_ICON_TYPE['magnet'] == 'magnets'
    assert catalog.HARDWARE_LABEL_ICON_TYPE['crimp_butt_splice'] == 'crimps'


def test_display_name():
    assert catalog.displayName('dowel') == 'Dowel'
    assert catalog.displayName('phillips_slot') == 'Phillips Slot'
    assert catalog.displayName('nut-square') == 'Nut square'


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('<svg/>')


def test_hardware_icons_come_from_the_folder(tmp_path):
    _touch(str(tmp_path / 'hardware' / 'washer.svg'))
    _touch(str(tmp_path / 'hardware' / 'dowel.svg'))
    _touch(str(tmp_path / 'hardware' / 'notes.txt'))
    icons = catalog.listHardwareIcons(str(tmp_path))
    assert icons == [('Washer', str(tmp_path / 'hardware' / 'washer.svg')), ('Dowel', str(tmp_path / 'hardware' / 'dowel.svg'))]


def test_hardware_icons_missing_folder(tmp_path):
    assert catalog.listHardwareIcons(str(tmp_path)) == []


def test_screw_options_come_from_file_names(tmp_path):
    _touch(str(tmp_path / 'screws' / 'screw_socket_machine_full_hex_noflange_nosec.svg'))
    _touch(str(tmp_path / 'screws' / 'screw_pan_tapping_full_phillips_slot_flange_sec.svg'))
    options = catalog.screwOptions(str(tmp_path))
    assert options['head'] == ['socket', 'pan']
    assert options['shaft'] == ['machine', 'tapping']
    assert options['threads'] == ['full']
    assert options['driver'] == ['phillips_slot', 'hex']
    assert options['flange'] == [False, True]
    assert options['security'] == [False, True]


def test_screw_icon_path(tmp_path):
    name = 'screw_socket_machine_full_hex_noflange_nosec.svg'
    _touch(str(tmp_path / 'screws' / name))
    assert catalog.screwIconPath(str(tmp_path), 'socket', 'machine', 'full', 'hex', False, False) == str(tmp_path / 'screws' / name)
    assert catalog.screwIconPath(str(tmp_path), 'socket', 'machine', 'partial', 'hex', False, False) is None
    assert catalog.screwOptions(str(tmp_path / 'nothing')) == {'head': [], 'shaft': [], 'threads': [], 'driver': [], 'flange': [], 'security': []}


def test_svg_size_from_width_and_height(tmp_path):
    path = tmp_path / 'a.svg'
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="14.5mm" height="10mm" viewBox="0 0 14.5 10"><path d="M0,0"/></svg>')
    assert catalog.svgSize(str(path)) == (14.5, 10.0)


def test_svg_size_from_view_box_only(tmp_path):
    path = tmp_path / 'b.svg'
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -2 13 7.5"><path d="M0,0"/></svg>')
    assert catalog.svgSize(str(path)) == (13.0, 7.5)


def test_svg_size_single_quotes_and_long_header(tmp_path):
    path = tmp_path / 'c.svg'
    path.write_text('<?xml version="1.0"?>\n<!-- ' + 'x' * 10000 + ' -->\n<svg xmlns="http://www.w3.org/2000/svg" width=\'12mm\' height=\'8mm\'><path d="M0,0"/></svg>')
    assert catalog.svgSize(str(path)) == (12.0, 8.0)


def test_display_names_are_the_ones_cullenect_shows():
    assert catalog.displayName('roundh') == 'Round'
    assert catalog.displayName('tnut_1') == 'T-Nut Side'
    assert catalog.displayName('tnut_2') == 'T-Nut Top'
    assert catalog.displayName('torx') == 'Torx/Star'
    assert catalog.displayName('square') == 'Robertson/Square'
    assert catalog.displayName('crimp_ring_open') == 'Crimp Ring - Open'
    assert catalog.displayName('tapping') == 'Tapping'


def test_every_building_block_and_hardware_has_a_cullenect_name():
    for key in catalog.HEADS + catalog.SHAFTS + catalog.THREADS + catalog.DRIVERS + catalog.CULLENECT_HARDWARE:
        assert key in catalog.CULLENECT_NAMES


def test_hardware_icons_in_cullenect_order_then_new_ones(tmp_path):
    for name in ('washer', 'nut', 'magnet', 'dowel', 'anchor'):
        _touch(str(tmp_path / 'hardware' / f'{name}.svg'))
    names = [name for (name, _) in catalog.listHardwareIcons(str(tmp_path))]
    assert names == ['Washer', 'Nut', 'Magnet', 'Anchor', 'Dowel']


def test_screw_options_in_cullenect_order(tmp_path):
    for name in ('screw_socket_machine_full_hex_noflange_nosec.svg', 'screw_pan_tapping_partial_slot_flange_sec.svg',
                 'screw_roundh_machine_full_phillips_noflange_nosec.svg', 'screw_none_machine_full_none_noflange_nosec.svg'):
        _touch(str(tmp_path / 'screws' / name))
    options = catalog.screwOptions(str(tmp_path))
    assert options['head'] == ['none', 'socket', 'roundh', 'pan']
    assert options['threads'] == ['full', 'partial']
    assert options['driver'] == ['none', 'slot', 'phillips', 'hex']


def _sized(tmp_path, width, height):
    path = tmp_path / 'sized.svg'
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><path d="M0,0"/></svg>')
    return str(path)


def test_svg_size_converts_units(tmp_path):
    assert catalog.svgSize(_sized(tmp_path, '1cm', '0.5cm')) == approx((10.0, 5.0))
    assert catalog.svgSize(_sized(tmp_path, '1in', '0.5in')) == approx((25.4, 12.7))
    assert catalog.svgSize(_sized(tmp_path, '72pt', '36pt')) == approx((25.4, 12.7))


def test_svg_size_without_unit_is_css_pixels(tmp_path):
    # an svg without units in width and height is in user units, CSS pixels of 1/96 in
    assert catalog.svgSize(_sized(tmp_path, '96', '48')) == approx((25.4, 12.7))
    assert catalog.svgSize(_sized(tmp_path, '96px', '48px')) == approx((25.4, 12.7))


def test_svg_size_percent_falls_back_to_the_view_box(tmp_path):
    path = tmp_path / 'p.svg'
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 13 7.5"><path d="M0,0"/></svg>')
    assert catalog.svgSize(str(path)) == (13.0, 7.5)


def test_shown_names_are_unique_per_choice():
    # the label dialog maps a shown name back to its key, two keys with one name would be mixed up
    for keys in (catalog.HEADS, catalog.SHAFTS, catalog.THREADS, catalog.DRIVERS, catalog.CULLENECT_HARDWARE):
        names = [catalog.displayName(key) for key in keys]
        assert len(set(names)) == len(names)
