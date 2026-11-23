from wasjetzt.ui.geometry import bottom_right_position


def test_bottom_right_with_margin():
    assert bottom_right_position(0, 0, 1920, 1040, 360, 180, 20) == (1540, 840)


def test_secondary_origin_and_taskbar_offset():
    assert bottom_right_position(-1920, 40, 1920, 1000, 360, 180, 20) == (-380, 840)


def test_window_larger_than_area_is_clamped():
    assert bottom_right_position(0, 0, 300, 100, 360, 180, 20) == (0, 0)
