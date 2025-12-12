from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import quote

from loguru import logger

from beaverhabits import utils


@dataclass
class StreakSquareStyle:
    decorations: list[str] = field(default_factory=list)
    color: str | None = None
    fill_rate: float | None = None
    interpolation: float | None = None
    label: str | None = None


def parse_text_decoration(tag: str, result: StreakSquareStyle) -> bool:
    # SKIP
    if tag == "skip":
        result.decorations.append("line-through")
        return True  # stop further processing

    # STAR or MARK
    if tag in ("star", "mark"):
        result.decorations.append("underline")
        return True

    return False


def parse_color(tag: str, result: StreakSquareStyle) -> bool:
    color = tag

    # quasar brand colors
    # https://quasar.dev/style/color-palette#brand-colors
    if tag in utils.COLORS:
        color = utils.COLORS[color]

    if match := utils.hex2rgb(color):
        r, g, b = match
        result.color = f"rgb({r},{g},{b})"

        return True

    return False


def parse_fill_rate(tag: str, result: StreakSquareStyle) -> bool:
    if not tag.startswith("_") or len(tag) < 2:
        return False

    if p := utils.parse_percentage(tag[1:]):
        result.fill_rate = p
        return True

    return False


def parse_brightness(tag: str, result: StreakSquareStyle) -> bool:
    if not tag.startswith("*") or len(tag) < 2:
        return False

    if p := utils.parse_percentage(tag[1:]):
        result.interpolation = p
        return True

    return False


def parse_label(tag: str, result: StreakSquareStyle) -> bool:
    # escape special characters in label
    if tag.startswith('"') and tag.endswith('"'):
        result.label = quote(tag[1:-1])
        return True

    result.label = quote(tag)

    return False


STYLE_PROCESSORS: list[Callable[[str, StreakSquareStyle], bool]] = [
    parse_text_decoration,
    parse_color,
    parse_fill_rate,
    parse_brightness,
    parse_label,
]


def update_square_style_context(tags: list[str], context: dict) -> dict[str, str]:
    result = StreakSquareStyle()

    for tag in tags:
        for processor in STYLE_PROCESSORS:
            if processor(tag.strip(), result):
                break

    if result.decorations:
        context["decoration"] = f"text-decoration: {" ".join(result.decorations)};"
    if result.color:
        context["fill_color"] = result.color
    if result.label:
        context["text"] = result.label
    if result.fill_rate is not None:
        context["mask_height"] = str(18 * (1 - result.fill_rate))
    if result.interpolation:
        logger.info(
            f"Adjusting fill color brightness by {result.interpolation*100:.1f}%"
        )
        if m := utils.hex2rgb(context.get("fill_color", "")):
            r, g, b = utils.adjust_color_brightness(*m, result.interpolation)
            context["fill_color"] = f"rgb({r},{g},{b})"

    return context
