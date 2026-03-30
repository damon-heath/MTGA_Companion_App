from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MainNavigation:
    sections: tuple[str, ...] = (
        "Dashboard",
        "Decks",
        "Matches",
        "Opponents",
        "Collection",
        "Exports",
        "Diagnostics",
        "Settings",
    )


def build_navigation(collection_enabled: bool) -> tuple[str, ...]:
    nav = list(MainNavigation().sections)
    if not collection_enabled:
        nav.remove("Collection")
    return tuple(nav)
