"""Palette B, "Graphite and Citrus", as an indah theme (ADR-0006).

Core roles restyle indah's own components. The ``x-`` extras carry the roles only this
dashboard has (explore versus exploit, the five disc colours); the board and pie read them as
``var(--x-...)``, so they follow indah's light and dark toggle with no code.
"""

import indah

DISCS = ("#f94144", "#f8961e", "#f9c74f", "#43aa8b", "#4d9de0")

THEME = indah.Theme(
    dark={
        "bg": "#0f1113",
        "surface": "#181b1f",
        "surface-2": "#121417",
        "surface-3": "#2a2f36",
        "text": "#eceff3",
        "muted": "#a0a8b3",
        "outline": "#2a2f36",
        "outline-soft": "#22262c",
        "primary": "#2ec4b6",
        "on-primary": "#0f1113",
    },
    light={
        "bg": "#f5f3ee",
        "surface": "#ffffff",
        "surface-2": "#ece9e2",
        "surface-3": "#d8d2c6",
        "text": "#1c1f23",
        "muted": "#5d646d",
        "outline": "#d8d2c6",
        "outline-soft": "#e6e2d9",
        "primary": "#1c1f23",
        "on-primary": "#ffffff",
    },
    extra_dark={
        "x-explore": "#ff9f1c",
        "x-exploit": "#2ec4b6",
        "x-gold": "#ffe66d",
        "x-pos": "#4895ef",
        "x-dot": "#7b8794",
        "x-heat-neg": "#ef476f",
        "x-heat-zero": "#2f353d",
        "x-heat-pos": "#2ec4b6",
        "x-rod": "#30363e",
        "x-base": "#2a2f36",
        **{f"x-disc-{i}": colour for i, colour in enumerate(DISCS)},
    },
    extra_light={
        "x-explore": "#f08a00",
        "x-exploit": "#1fa99c",
        "x-gold": "#d9a300",
        "x-pos": "#2f74d0",
        "x-dot": "#9aa1ab",
        "x-heat-neg": "#d63a5f",
        "x-heat-zero": "#ddd8cd",
        "x-heat-pos": "#1fa99c",
        "x-rod": "#cfc9bd",
        "x-base": "#d8d2c6",
        **{f"x-disc-{i}": colour for i, colour in enumerate(DISCS)},
    },
    radius="14px",
)
