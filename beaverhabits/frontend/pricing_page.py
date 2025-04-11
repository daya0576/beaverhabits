from nicegui import ui
from paddle_billing import Client, Environment, Options

from beaverhabits import const
from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.javascript import PADDLE_JS
from beaverhabits.frontend.menu import redirect
from beaverhabits.logging import logger
from beaverhabits.plan import plan

IMAGES = [
    "/statics/images/pricing/331492565-0418fa41-8985-46ef-b623-333b62b2f92e.jpg",
    "/statics/images/pricing/331492564-c0ce98cf-5a44-4bbc-8cd3-c7afb20af671.jpg",
    "/statics/images/pricing/331492575-516c19ca-9f55-4c21-9e6d-c8f0361a5eb2.jpg",
]

FREE, PRO = "Free $0", "Pro $9.9"
PLANS = {
    FREE: {
        "Key features": [
            "Add notes/descriptions",
            "Export & Import",
            "RESTful API",
            "Community support",
        ],
    },
    PRO: {
        "Buy lifetime license": [
            "Unlimited habits",
            "Daily backup",
            "14-day policy return",
            "Priority support",
        ],
    },
}
ACTIONS = {
    FREE: lambda: ui.button(
        "Get Started", on_click=lambda: ui.navigate.to("/register", new_tab=True)
    ),
    PRO: lambda: ui.button("Upgrade").on_click(lambda: plan.checkout()),
}

YOUTUBE = """
<iframe width="640" height="360" src="https://www.youtube.com/embed/4a16FmkGV6Y?si=OD2nNtIOqWTdBSp-" title="YouTube video player" color="white" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen</iframe>
"""


def link(text: str, url: str):
    return ui.link(target=url, new_tab=True).classes("max-sm:hidden").tooltip(text)


def description(is_pro: bool):
    with ui.row().classes("w-full"):
        ui.label("Beaver Habit Tracker").classes("text-3xl font-bold")
        ui.space()

        with link("Login", "/login"):
            ui.html(icons.LOGIN).classes("fill-white scale-125 m-1")
        with link("GitHub", const.HOME_PAGE):
            ui.html(icons.GITHUB).classes("fill-white scale-125 m-1")

    ui.label("A minimalistic habit tracking app without 'Goals'").classes(
        "text-lg text-center"
    )
    with ui.grid(columns=2).classes("w-full"):
        for plan, features in PLANS.items():
            with ui.card().props("bordered gap-1") as card:
                card.style("border-radius: 10px")
                card.classes("gap-2")
                price_label = ui.label(plan).classes("text-2xl font-bold")
                for feature, description in features.items():
                    ui.label(feature).classes("text-lg")
                    with ui.column().classes("gap-1"):
                        for desc in description:
                            with ui.row().classes("gap-1"):
                                ui.icon(icons.DONE).classes("place-self-center")
                                ui.label(desc)
                ui.space().classes("h-0")
                btn = ACTIONS[plan]()

            async def set_latest_price():
                if is_pro:
                    btn.set_text("Already Pro")
                    btn.disable()
                else:
                    logger.debug("Starting to set latest price")
                    price = await get_product_price()
                    logger.debug(f"Latest price: {price_label.text}")
                    text = f"Pro ${price:.2f}"
                    price_label.set_text(text)

            if plan == PRO:
                ui.timer(1, lambda: set_latest_price(), once=True)


def demo(*args):
    ui.label("How to keep your habits on track?").classes("text-2xl font-bold")
    with ui.column().classes("w-full gap-2"):
        reasons = [
            "Make it <b>obvious</b>: visual cues like the streak remind you to act again",
            "Make it <b>attractive</b>: the most effective form of motivation is progress",
            "Make it <b>satisfying</b>: tracking can become its own form of reward",
        ]
        for reason in reasons:
            ui.html(reason).style("font-size: 1rem; margin: 0px !important;")
    with ui.grid(columns=3).classes("w-full gap-1"):
        for image in IMAGES:
            ui.image(source=image)


def how_to_use(*args):
    with ui.row().classes("w-full"):
        ui.label("How to Use").classes("text-2xl font-bold")
        ui.space()
        ui.button("Try Demo").props("flat").on_click(
            lambda: ui.navigate.to("/demo", new_tab=True)
        )
    ui.html(YOUTUBE)


def footer():
    with ui.row().classes("w-full"):
        ui.space()
        ui.link(
            "Wiki", target="https://github.com/daya0576/beaverhabits/wiki", new_tab=True
        ).classes("text-primary")
        ui.link("Contact", target="mailto:daya0576@gmail.com", new_tab=True).classes(
            "text-primary"
        )
        ui.link("Privacy Policy", target="/privacy", new_tab=True).classes(
            "text-primary"
        )
        ui.link("Terms of Service", target="/terms", new_tab=True).classes(
            "text-primary"
        )
        ui.space()


async def get_product_price():
    sandbox = Environment.SANDBOX if settings.PADDLE_SANDBOX else Environment.PRODUCTION
    paddle = Client(settings.PADDLE_API_TOKEN, options=Options(sandbox))
    price_entity = paddle.prices.get(settings.PADDLE_PRICE_ID)
    return int(price_entity.unit_price.amount) / 100


async def landing_page(is_pro: bool) -> None:
    with ui.row().classes("max-w-2xl mx-auto w-full"):
        for section in (description, demo, how_to_use):
            with ui.card().classes("w-full").props("flat"):
                section(is_pro)

        footer()

    ui.add_css("body { background-color: #121212; color: white;  }")
    ui.add_head_html(PADDLE_JS)
