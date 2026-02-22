from nicegui import ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.frontend.layout import layout


def _mapping_to_chips(mapping: dict[str, str]) -> list[str]:
    """Convert {"yes": "red"} to ["yes:red"]"""
    return [f"{k}:{v}" for k, v in mapping.items()]


def _chips_to_mapping(chips: list[str]) -> dict[str, str]:
    """Convert ["yes:red"] to {"yes": "red"}"""
    mapping = {}
    for chip in chips:
        if ":" in chip:
            k, v = chip.split(":", 1)
            if k.strip() and v.strip():
                mapping[k.strip()] = v.strip()
    return mapping


async def chip_sets_page(user: User):
    configs = await views.get_user_configs(user)
    current_chips = configs.default_chips or []
    current_mapping = configs.default_chips_mapping or {}

    with layout():
        with ui.column().classes("w-full max-w-[600px] px-4 gap-4"):
            # Header
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Completion Status").classes("text-lg font-medium")
                ui.link(
                    "Docs ↗",
                    "https://github.com/daya0576/beaverhabits/wiki/Daily-Notes-&-Descriptions#streak-customization",
                    new_tab=True,
                ).classes("text-sm opacity-50 no-underline hover:underline")

            ui.separator().classes("opacity-30")

            # Section 1: Default status
            with ui.column().classes("w-full gap-1"):
                ui.label("Default Status").classes("text-sm font-medium opacity-80")
                ui.label(
                    "Default status buttons shown in the note dialog (e.g. yes, no, skip)."
                ).classes("text-xs opacity-50")
                chips_input = ui.input_chips(
                    "e.g. yes, no, skip",
                    value=current_chips,
                    new_value_mode="add-unique",
                ).classes("w-full")

            ui.separator().classes("opacity-30")

            # Section 2: Custom status
            with ui.column().classes("w-full gap-1"):
                ui.label("Custom Status").classes("text-sm font-medium opacity-80")
                ui.label(
                    "Map a status to tags that are auto-appended to the note on click."
                ).classes("text-xs opacity-50")
                mapping_input = ui.input_chips(
                    "e.g. skip:#amber #skip",
                    value=_mapping_to_chips(current_mapping),
                    new_value_mode="add-unique",
                ).classes("w-full")

            async def save_chips():
                mapping = _chips_to_mapping(mapping_input.value)
                await views.update_default_chips(user, chips_input.value, mapping)
                ui.notify("Saved", color="positive")

            ui.button("Save", on_click=save_chips).props("flat dense")
