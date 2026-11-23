"""Punct de intrare: argumente, logging, single-instance, pornirea controller-ului."""
from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from wasjetzt import APP_NAME, paths


def _setup_logging() -> None:
    handlers: list[logging.Handler] = []
    try:
        paths.logs_dir().mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(paths.logs_dir() / "wasjetzt.log", maxBytes=512_000,
                                            backupCount=2, encoding="utf-8"))
    except OSError:
        pass
    # Atenție: logurile NU conțin textul răspunsurilor utilizatorului.
    logging.basicConfig(level=logging.INFO, handlers=handlers or None,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("--background", action="store_true", help="pornire în fundal (folosit la startup)")
    args, _unknown = parser.parse_known_args(argv)

    _setup_logging()
    from PySide6.QtWidgets import QApplication

    from wasjetzt.app import AppController
    from wasjetzt.os_integration.windows_mutex import create_app_mutex
    from wasjetzt.single_instance import SingleInstance

    qapp = QApplication(sys.argv[:1])
    qapp.setApplicationName(APP_NAME)
    qapp.setQuitOnLastWindowClosed(False)

    guard = SingleInstance()
    if not guard.acquire():
        return 0  # o instanță rulează deja; a fost anunțată să-și arate fereastra
    create_app_mutex()

    controller = AppController(qapp, background=args.background)
    guard.activated.connect(controller.open_main)
    if not controller.start():
        return 0
    return qapp.exec()
