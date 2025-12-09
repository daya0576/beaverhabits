from dataclasses import dataclass, field
from typing import Callable

from loguru import logger

from beaverhabits import utils


@dataclass
class StreakSquareStyle:
    decorations: list[str] = field(default_factory=list)
    color: str | None = None
    process: float | None = None
    label: str | None = None


def get_text_decoration(tag: str, result: StreakSquareStyle) -> bool:
    # SKIP
    if tag == "skip":
        result.decorations.append("line-through")
        return True  # stop further processing

    # STAR or MARK
    if tag in ("star", "mark"):
        result.decorations.append("underline")
        return True

    return False


def get_color(tag: str, result: StreakSquareStyle) -> bool:
    hex_color = tag
    if tag in utils.COLORS:
        hex_color = utils.COLORS[tag]

    if match := utils.hex2rgb(hex_color):
        r, g, b = match
        result.color = f"rgb({r},{g},{b})"
        return True

    return False


def get_process(tag: str, result: StreakSquareStyle) -> bool:
    # 1/4 or 30%
    if "/" in tag:
        try:
            numerator, denominator = map(float, tag.split("/"))
            result.process = numerator / denominator
            return True
        except ValueError:
            pass

    if tag.endswith("%"):
        try:
            percent_value = float(tag[:-1])
            result.process = percent_value / 100.0
            return True
        except ValueError:
            pass

    return False


def get_label(tag: str, result: StreakSquareStyle) -> bool:
    result.label = tag
    return False


STYLE_PROCESSORS: list[Callable[[str, StreakSquareStyle], bool]] = [
    get_text_decoration,
    get_color,
    get_process,
    get_label,
]


def build_square_style_context(tags: list[str]) -> dict[str, str]:
    result = StreakSquareStyle()

    for tag in tags:
        for processor in STYLE_PROCESSORS:
            if processor(tag.strip(), result):
                break

    context = {}
    if result.decorations:
        context["decoration"] = f"text-decoration: {" ".join(result.decorations)};"
    if result.color:
        context["fill_color"] = result.color
    if result.label:
        context["text"] = result.label
    if result.process is not None:
        context["mask_height"] = str(18 * (1 - result.process))

    logger.info(f"Built square style context: {context}")
    return context
