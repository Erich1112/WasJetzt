import pytest

from wasjetzt.os_integration.windows_startup import (BACKGROUND_ARG, RUN_KEY, VALUE_NAME,
                                                     WindowsStartupService, build_command)
from wasjetzt.services.startup_service import StartupError, UnsupportedStartupService


class FakeRegistry:
    def __init__(self, fail=False):
        self.data = {(RUN_KEY, "AltProgram"): '"C:\\Alt\\alt.exe"'}
        self.fail = fail

    def get(self, key, name):
        return self.data.get((key, name))

    def set(self, key, name, value):
        if self.fail:
            raise PermissionError("acces refuzat")
        self.data[(key, name)] = value

    def delete(self, key, name):
        if self.fail:
            raise PermissionError("acces refuzat")
        self.data.pop((key, name), None)


CMD = '"C:\\Users\\Ana Ștefan\\AppData\\Local\\Programs\\WasJetzt\\WasJetzt.exe" --background'


def test_enable_creates_run_entry_with_quoted_path():
    reg = FakeRegistry()
    svc = WindowsStartupService(registry=reg, command=CMD)
    assert svc.is_enabled() is False
    svc.enable()
    assert svc.is_enabled() and reg.data[(RUN_KEY, VALUE_NAME)] == CMD and svc.is_up_to_date()


def test_disable_removes_only_our_entry():
    reg = FakeRegistry()
    svc = WindowsStartupService(registry=reg, command=CMD)
    svc.enable()
    svc.disable()
    assert not svc.is_enabled()
    assert (RUN_KEY, "AltProgram") in reg.data  # intrările altor aplicații rămân neatinse
    svc.disable()  # idempotent


def test_failure_is_reported_not_faked():
    svc = WindowsStartupService(registry=FakeRegistry(fail=True), command=CMD)
    with pytest.raises(StartupError):
        svc.enable()
    assert svc.is_enabled() is False


def test_stale_entry_is_detected_and_repaired():
    reg = FakeRegistry()
    reg.data[(RUN_KEY, VALUE_NAME)] = '"D:\\vechi\\WasJetzt.exe" --background'
    svc = WindowsStartupService(registry=reg, command=CMD)
    assert svc.is_enabled() and not svc.is_up_to_date()
    svc.enable()
    assert svc.is_up_to_date()


def test_build_command_frozen_and_source():
    assert build_command(frozen=True, executable="C:\\Program Files\\WasJetzt\\WasJetzt.exe") == \
        f'"C:\\Program Files\\WasJetzt\\WasJetzt.exe" {BACKGROUND_ARG}'
    assert build_command(frozen=False, executable="/usr/bin/python3").endswith(f"-m wasjetzt {BACKGROUND_ARG}")


def test_unsupported_platform_service():
    svc = UnsupportedStartupService()
    assert not svc.is_supported() and not svc.is_enabled()
    with pytest.raises(StartupError):
        svc.enable()
