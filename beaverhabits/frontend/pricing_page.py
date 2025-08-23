from nicegui import ui
from paddle_billing import Client, Environment, Options

from beaverhabits import const
from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import redirect
from beaverhabits.frontend.css import YOUTUBE_CSS
from beaverhabits.frontend.javascript import PADDLE_JS
from beaverhabits.frontend.layout import custom_headers
from beaverhabits.plan import plan

IMAGES = [
    "/statics/images/pricing/331492565-0418fa41-8985-46ef-b623-333b62b2f92e.jpg",
    "/statics/images/pricing/331492564-c0ce98cf-5a44-4bbc-8cd3-c7afb20af671.jpg",
    "/statics/images/pricing/331492575-516c19ca-9f55-4c21-9e6d-c8f0361a5eb2.jpg",
]

FREE, PRO = "Basic $0", "Pro $9.9"
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
            "Organize habits by category",
            "Daily backup",
            "14-day policy return",
        ],
    },
}
ACTIONS = {
    FREE: lambda: ui.button("Get Started", on_click=lambda: redirect("/login")),
    PRO: lambda: ui.button("Upgrade").on_click(lambda: plan.checkout()),
}

YOUTUBE = """
<iframe src="https://www.youtube.com/embed/4a16FmkGV6Y?si=OD2nNtIOqWTdBSp-" 
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowfullscreen></iframe>
"""


def get_product_price():
    sandbox = Environment.SANDBOX if settings.PADDLE_SANDBOX else Environment.PRODUCTION
    paddle = Client(settings.PADDLE_API_TOKEN, options=Options(sandbox))
    price_entity = paddle.prices.get(settings.PADDLE_PRICE_ID)
    return int(price_entity.unit_price.amount) / 100


def link(text: str, url: str, new_tab: bool = False, tooltip=""):
    link = ui.link(text=text, target=url, new_tab=new_tab)
    link.classes("dark:text-white no-underline hover:no-underline")
    if tooltip:
        link.tooltip(tooltip)
    return link


def icon(text: str, url: str, icon_str: str, tooltip: str):
    with link(text, url, tooltip=tooltip).classes("max-sm:hidden"):
        ui.icon(icon_str).classes("text-3xl")


def description():
    with ui.row().classes("w-full"):
        link("Beaver Habit Tracker", const.GUI).classes("text-3xl font-bold")
        ui.space()
        icon("", "/login", "sym_r_login", tooltip="Login")
        icon("", const.HOME_PAGE, "eva-github", tooltip="Star us on Github!")

    desc = ui.label("Simple habit tracking app without 'Goals'")
    desc.classes("text-lg text-center")

    with ui.row().classes("w-full grid grid-cols-1 sm:grid-cols-2 gap-3"):
        for plan_name, features in PLANS.items():
            with ui.card().props("flat").classes("gap-2"):
                price_label = ui.label(plan_name).classes("text-2xl font-bold")
                for feature, description in features.items():
                    ui.label(feature).classes("text-lg")
                    with ui.column().classes("gap-1"):
                        for desc in description:
                            with ui.row().classes("gap-1"):
                                ui.icon(icons.DONE).classes("place-self-center")
                                ui.label(desc)
                ui.space().classes("h-0")
                btn = ACTIONS[plan_name]()

            async def set_latest_price():
                if await plan.check_pro():
                    btn.set_text("Already Pro")
                    btn.props("flat")
                    btn.disable()

                price_label.set_text(f"Pro ${get_product_price():.2f}")

            if plan_name == PRO:
                ui.context.client.on_connect(set_latest_price)


def demo():
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


def how_to_use():
    with ui.row().classes("w-full"):
        ui.label("How to Use").classes("text-2xl font-bold")
        ui.space()
        ui.button("Try Demo").props("flat").on_click(
            lambda: ui.navigate.to("/demo", new_tab=True)
        )

    ui.html(YOUTUBE).classes("videowrapper")


def why_user_love():
    ui.label("Why users ❤️ BeaverHabits").classes("text-2xl font-bold")
    comments = [
        "I love this idea. I like the simplicity and the lack of ‘Goals’, which always trigger me.",
        "Great job i like that is simple and aesthetic and not overwhelmed with soo much options.",
        "Both this and Loop Habit Tracker are exactly what I was looking for. Well done. Oh, and dope choice of name. I also put a ton of time into that game, haha.",
        "There are many habit-tracking tools out there, but the beauty of Beaver Habit Tracker is its amazing simplicity. It just runs on any browser on your PC or mobile, and it just does the job.",
    ]

    with ui.column().classes("w-full gap-1"):
        for comment in comments:
            # ui.label(f'> "{comment}"')
            ui.markdown(f"> {comment}")

        ui.markdown(f"> ...")


def footer():
    with ui.row().classes("w-full"):
        ui.space()
        link = lambda text, url: ui.link(text, url, True).classes("text-primary")
        link("Wiki", "https://github.com/daya0576/beaverhabits/wiki")
        link("Contact", "mailto:daya0576@gmail.com")
        link("Privacy Policy", "/privacy")
        link("Terms of Service", "/terms")
        ui.space()


async def landing_page() -> None:
    with ui.row().classes("max-w-2xl mx-auto w-full"):
        description()
        for section in (demo, how_to_use, why_user_love):
            with ui.card().classes("w-full").props("flat"):
                section()

        footer()

    ui.add_head_html(PADDLE_JS)
    ui.add_css(YOUTUBE_CSS)
    custom_headers()

    ui.add_head_html(
        '<link href="https://unpkg.com/eva-icons@1.1.3/style/eva-icons.css" rel="stylesheet" />'
    )
