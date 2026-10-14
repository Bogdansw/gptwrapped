from typing import Dict

ICON_PATHS: Dict[str, str] = {
    "hole": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="12" r="4.5"/>'
        '<circle cx="12" cy="12" r="0.8" fill="currentColor" stroke="none"/>'
    ),
    "moon": (
        '<path d="M21 12.79A9 9 0 1 1 11.21 3A7 7 0 0 0 21 12.79z"/>'
    ),
    "sunrise": (
        '<path d="M17 18a5 5 0 0 0-10 0"/>'
        '<line x1="12" y1="9" x2="12" y2="2"/>'
        '<line x1="4.22" y1="10.22" x2="5.64" y2="11.64"/>'
        '<line x1="1" y1="18" x2="23" y2="18"/>'
        '<line x1="18.36" y1="11.64" x2="19.78" y2="10.22"/>'
        '<polyline points="8 6 12 2 16 6"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="12" r="5"/>'
        '<circle cx="12" cy="12" r="1"/>'
    ),
    "bars": (
        '<line x1="12" y1="20" x2="12" y2="10"/>'
        '<line x1="18" y1="20" x2="18" y2="4"/>'
        '<line x1="6" y1="20" x2="6" y2="16"/>'
    ),
    "zap": (
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
    ),
    "trend": (
        '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>'
        '<polyline points="17 6 23 6 23 12"/>'
    ),
}


def get_icon_svg(name: str, size: int = 22) -> str:
    inner = ICON_PATHS.get(name, ICON_PATHS["zap"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        f'{inner}</svg>'
    )
