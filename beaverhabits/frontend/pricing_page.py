from nicegui import ui

from beaverhabits.frontend import icons

IMAGES = [
    "/statics/images/pricing/331492565-0418fa41-8985-46ef-b623-333b62b2f92e.jpg",
    "/statics/images/pricing/331492564-c0ce98cf-5a44-4bbc-8cd3-c7afb20af671.jpg",
    "/statics/images/pricing/331492575-516c19ca-9f55-4c21-9e6d-c8f0361a5eb2.jpg",
]

PLANS = {
    "Free $0": {
        "Key features": [
            "Add notes/descriptions",
            "Export & Import",
            "RESTful API",
            "Community support",
        ],
    },
    "Plus $9.9": {
        "Buy lifetime license": [
            "Unlimited habits",
            "Daily backup",
            "Priority support",
        ],
    },
}
ACTIONS = {
    "Free $0": lambda: ui.button(
        "Sign up", on_click=lambda: ui.navigate.to("/register", new_tab=True)
    ).props("flat"),
    "Plus $9.9": lambda: ui.button("Get started"),
}


def description():
    ui.label("Beaver Habit Tracker").classes("text-3xl font-bold")
    ui.label("A minimalistic habit tracking app without 'Goals'").classes(
        "text-lg text-center"
    )
    with ui.grid(columns=3).classes("w-full gap-1"):
        for image in IMAGES:
            ui.image(source=image)

    ui.button("Try Demo").props("flat").on_click(lambda: ui.navigate.to("/demo"))


def pricing():
    ui.label("Pricing Plans").classes("text-3xl font-bold")
    ui.space()
    # ui.label("To support an indie and full-time parent ❤️👶").classes(
    #     "text-lg text-center"
    # )
    with ui.grid(columns=2).classes("w-full"):
        for plan, features in PLANS.items():
            with ui.card().props("flat bordered") as card:
                card.style("border-radius: 8px")
                card.classes("gap-2")
                ui.label(plan).classes("text-2xl font-bold")
                for feature, description in features.items():
                    ui.label(feature).classes("text-lg")
                    with ui.column().classes("gap-0"):
                        for desc in description:
                            with ui.row().classes("gap-1"):
                                ui.icon(icons.DONE).classes("place-self-center")
                                ui.label(desc)
                ui.space()
                ACTIONS[plan]()


def footer():
    with ui.row().classes("w-full"):
        ui.space()
        ui.link(
            "Wiki", target="https://github.com/daya0576/beaverhabits/wiki", new_tab=True
        )
        ui.link("Contact", target="mailto:daya0576@gmail.com", new_tab=True)
        ui.link("Privacy Policy", target="/privacy", new_tab=True)
        ui.link("Terms of Service", target="/terms", new_tab=True)
        ui.space()


async def landing_page() -> None:
    with ui.row().classes("max-w-xl mx-auto w-full"):
        with ui.card().classes("w-full gap-2").props("flat"):
            pricing()
        with ui.card().classes("w-full gap-2").props("flat"):
            description()
    footer()
