import json

import pytest

from wasjetzt.config.settings import Settings, SettingsError, SettingsManager, validate


def test_first_run_creates_defaults(tmp_path):
    mgr = SettingsManager(tmp_path / "settings.json")
    s = mgr.load()
    assert mgr.first_run is True
    assert s.interval_minutes == 60 and s.configured is False and s.on_dismiss == "wait_next_interval"
    assert not (tmp_path / "settings.json").exists()  # nu scrie nimic până la salvare explicită


def test_valid_settings_roundtrip(tmp_path):
    path = tmp_path / "cfg" / "settings.json"
    mgr = SettingsManager(path)
    mgr.load()
    s = Settings(configured=True, export_directory=str(tmp_path / "ex ăö"), interval_minutes=30)
    mgr.save(s)
    loaded = SettingsManager(path).load()
    assert loaded.interval_minutes == 30 and loaded.configured is True
    assert loaded.export_directory == str(tmp_path / "ex ăö")
    assert json.loads(path.read_text("utf-8"))["schema_version"] == 1


def test_invalid_json_does_not_crash_and_is_not_lost(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ nu e json", encoding="utf-8")
    mgr = SettingsManager(path)
    s = mgr.load()
    assert s.interval_minutes == 60 and mgr.load_error
    assert path.read_text(encoding="utf-8") == "{ nu e json"  # neatins la citire
    mgr.save(Settings(configured=True))
    assert list(tmp_path.glob("settings.json.bak-*"))  # copie de siguranță înainte de suprascriere


def test_invalid_field_falls_back_individually(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"interval_minutes": 2, "start_minimized": False, "configured": True}), "utf-8")
    mgr = SettingsManager(path)
    s = mgr.load()
    assert s.interval_minutes == 60 and "interval_minutes" in mgr.load_warnings
    assert s.start_minimized is False and s.configured is True


@pytest.mark.parametrize("value,ok", [(4, False), (5, True), (60, True), (1440, True), (1441, False),
                                      (True, False), ("60", False), (0, False), (-5, False)])
def test_interval_limits(value, ok):
    errors = validate(Settings(interval_minutes=value))
    assert ("interval_minutes" not in errors) is ok


def test_save_rejects_invalid(tmp_path):
    mgr = SettingsManager(tmp_path / "s.json")
    with pytest.raises(SettingsError):
        mgr.save(Settings(interval_minutes=3))
    assert not (tmp_path / "s.json").exists()


def test_export_directory_change_is_saved_and_unknown_keys_kept(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"configured": True, "future_option": 7}), "utf-8")
    mgr = SettingsManager(path)
    s = mgr.load()
    s.export_directory = str(tmp_path / "nou")
    mgr.save(s)
    data = json.loads(path.read_text("utf-8"))
    assert data["export_directory"] == str(tmp_path / "nou") and data["future_option"] == 7
