"""Calcule de poziționare fără Qt (testabile)."""
from __future__ import annotations


def bottom_right_position(avail_x: int, avail_y: int, avail_w: int, avail_h: int,
                          win_w: int, win_h: int, margin: int = 20) -> tuple[int, int]:
    """Colțul din dreapta-jos al zonei de lucru, cu margine; fereastra nu iese niciodată din zonă."""
    x = avail_x + avail_w - win_w - margin
    y = avail_y + avail_h - win_h - margin
    return max(avail_x, x), max(avail_y, y)
