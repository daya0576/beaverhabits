import time
from contextlib import contextmanager

from nicegui import background_tasks, ui

from beaverhabits import views
from beaverhabits.app.auth import user_logout
from beaverhabits.configs import settings
from beaverhabits.frontend import css, icons
from beaverhabits.frontend.components import (
    compat_card,
    habit_edit_dialog,
    menu_header,
    menu_icon_button,
    menu_icon_item,
    redirect,
    separator,
)
from beaverhabits.frontend.javascript import PREVENT_CONTEXT_MENU
from beaverhabits.frontend.menu import add_menu, sort_menu, stats_date_pick_menu
from beaverhabits.plan import plan
from beaverhabits.storage.meta import (
    get_root_path,
    is_page_demo,
    page_path,
    page_title,
)
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.version import IDENTITY


def pwa_headers():
    # Extend background to iOS notch
    ui.add_head_html(
        """
        <link rel="apple-touch-icon" href="/statics/images/apple-touch-icon-v4.png">
        
        <meta name="apple-mobile-web-app-title" content="Beaver">
        <meta name="application-name" content="Beaver">
        
        <meta name="theme-color" content="#F9F9F9" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#121212" media="(prefers-color-scheme: dark)" />
        """
    )

    # Experimental PWA
    if settings.ENABLE_IOS_STANDALONE:
        # Hiding Safari User Interface Components
        ui.add_head_html('<meta name="mobile-web-app-capable" content="yes">')
        ui.add_head_html('<link rel="manifest" href="/statics/pwa/manifest.json">')


def custom_headers():
    # Get current page info
    page_url = "https://beaverhabits.com" + page_path()

    # SEO meta tags
    ui.add_head_html(
        f"""
        <!-- Basic Meta Tags -->
        <meta name="description" content="A minimal habit tracking app without Goals. Track your daily habits with a simple, privacy-focused interface.">
        <meta name="keywords" content="habit tracker, habit tracking, self-hosted, productivity, daily habits, habit building, open source">
        <meta name="author" content="daya0576">
        <meta name="robots" content="index, follow">
        <link rel="canonical" href="{page_url}">
        
        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="website">
        <meta property="og:url" content="{page_url}">
        <meta property="og:title" content="Beaver Habit Tracker">
        <meta property="og:description" content="A minimal habit tracking app without Goals. Track your daily habits with privacy and simplicity.">
        <meta property="og:image" content="https://beaverhabits.com/statics/images/apple-touch-icon-v4.png">
        <meta property="og:site_name" content="Beaver Habit Tracker">
        
        <!-- Twitter -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:url" content="{page_url}">
        <meta name="twitter:title" content="Beaver Habit Tracker">
        <meta name="twitter:description" content="A minimal habit tracking app without Goals. Track your daily habits with privacy and simplicity.">
        <meta name="twitter:image" content="https://beaverhabits.com/statics/images/apple-touch-icon-v4.png">
        
        <!-- Structured Data (JSON-LD) -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Beaver Habit Tracker",
            "url": "https://beaverhabits.com",
            "description": "A minimal habit tracking app without Goals",
            "applicationCategory": "ProductivityApplication",
            "operatingSystem": "Web, iOS, Android",
            "offers": {{
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD"
            }},
            "author": {{
                "@type": "Person",
                "name": "daya0576",
                "url": "https://github.com/daya0576"
            }}
        }}
        </script>
        """
    )

    # Long-press event
    ui.add_head_html('<script src="/statics/libs/long-press-event.min.js"></script>')

    # Analytics
    if settings.UMAMI_ANALYTICS_ID:
        ui.add_head_html(
            f'<script defer src="{settings.UMAMI_SCRIPT_URL}" data-website-id="{settings.UMAMI_ANALYTICS_ID}"></script>'
        )

    # Prevent white flash on page load
    ui.add_css(css.WHITE_FLASH_PREVENT)
    ui.add_css(css.TEXTAREA_CSS)

    # prevent context menu
    ui.add_body_html(f"<script>{PREVENT_CONTEXT_MENU}</script>")

    # custom css styles
    views.apply_theme_style()

    # Green martian terminal theme
    ui.add_head_html(
        """
        <style>
        /* Green martian terminal theme */
        :root, body {
            --q-primary: #00ff66;
            --q-secondary: #1f8a4c;
            --q-accent: #00ff41;
        }

        body, h1, h2, h3, h4, h5, h6,
        input, textarea, select, button,
        .q-btn, .q-field, .q-item, .q-card, .q-menu, .q-dialog {
            font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace !important;
        }

        body, body.body--dark, .q-layout, .q-page-container, .q-page {
            background-color: #040804 !important;
            color: #00ff41;
        }

        h1, h2, h3, h4, h5, h6, a {
            color: #00ff41 !important;
            text-shadow: 0 0 6px rgba(0, 255, 65, 0.35);
        }

        .text-grey, .text-muted, .q-item__label--caption {
            color: #1f8a4c !important;
        }

        .q-card {
            background-color: #0a100a !important;
            border: 1px solid #123f1f !important;
            box-shadow: 0 0 12px rgba(0, 255, 65, 0.06) !important;
            color: #00ff41;
        }

        .q-checkbox .q-checkbox__label,
        .q-checkbox {
            color: #1f8a4c;
        }
        .q-checkbox.q-checkbox--active,
        .q-checkbox.q-checkbox--active .q-checkbox__label,
        .q-checkbox.q-checkbox--active .q-checkbox__inner {
            color: #00ff66 !important;
            text-shadow: 0 0 6px rgba(0, 255, 102, 0.5);
            filter: drop-shadow(0 0 3px rgba(0, 255, 102, 0.4));
        }

        .q-btn {
            background-color: #0a140a !important;
            border: 1px solid #123f1f !important;
            color: #00ff41 !important;
            box-shadow: none !important;
        }
        .q-btn:hover {
            border-color: #00ff66 !important;
            box-shadow: 0 0 8px rgba(0, 255, 102, 0.25) !important;
        }
        .q-btn.bg-primary, .q-btn--primary, .q-btn.text-primary {
            background-color: #0a140a !important;
            border-color: #00ff66 !important;
            color: #00ff66 !important;
        }

        .q-header {
            background-color: #030603 !important;
            border-bottom: 1px solid #123f1f !important;
        }

        .q-dialog .q-card, .q-menu {
            background-color: #0a100a !important;
            border: 1px solid #123f1f !important;
            color: #00ff41;
        }
        .q-item {
            background-color: transparent;
            color: #00ff41;
        }
        .q-item:hover, .q-item.q-item--active {
            background-color: #0d1a0d !important;
        }

        .q-input .q-field__control,
        .q-select .q-field__control,
        .q-textarea .q-field__control,
        .q-field .q-field__control {
            background-color: #060a06 !important;
            border: 1px solid #123f1f !important;
            color: #00ff41 !important;
        }
        .q-field__native, .q-field__input, .q-field__label {
            color: #00ff41 !important;
            caret-color: #00ff41;
        }
        .q-field__label {
            color: #1f8a4c !important;
        }

        .q-toggle.q-toggle--active .q-toggle__inner,
        .q-toggle.q-toggle--active .q-toggle__track,
        .q-toggle.q-toggle--active .q-toggle__thumb {
            color: #00ff66 !important;
        }
        .q-toggle.q-toggle--active .q-toggle__track {
            background-color: #123f1f !important;
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #040804;
        }
        ::-webkit-scrollbar-thumb {
            background: #123f1f;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #1f8a4c;
        }
        html {
            scrollbar-color: #123f1f #040804;
        }

        ::selection {
            background: #00ff41;
            color: #040804;
        }

        /* Scanlines overlay; pointer-events none so it never blocks clicks. */
        body::after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 99999;
            background: repeating-linear-gradient(
                to bottom,
                rgba(0, 255, 65, 0.03) 0px,
                rgba(0, 255, 65, 0.03) 1px,
                transparent 1px,
                transparent 3px
            );
        }

        /* Fixes for components still using the app primary rgb(88, 152, 212). */
        .q-checkbox__inner:before {
            border-color: #1f8a4c !important;
            color: #1f8a4c !important;
        }
        .q-checkbox__inner:hover:before {
            border-color: #00ff66 !important;
        }
        .q-checkbox[aria-checked="true"] .q-checkbox__inner:before,
        .q-checkbox--active .q-checkbox__inner:before {
            border-color: #00ff66 !important;
            color: #00ff66 !important;
            box-shadow: 0 0 6px rgba(0, 255, 102, 0.4);
        }
        .q-checkbox__inner svg,
        .q-checkbox__inner svg path {
            fill: #00ff66 !important;
            stroke: #00ff66 !important;
        }

        .text-primary {
            color: #00ff66 !important;
        }
        .bg-primary {
            background-color: #00ff66 !important;
        }

        .q-btn.text-primary,
        .q-btn .q-icon,
        .q-btn__content {
            color: #00ff41 !important;
        }

        .q-toggle .q-toggle__inner {
            color: #1f8a4c !important;
        }
        .q-toggle[aria-checked="true"] .q-toggle__inner,
        .q-toggle.q-toggle--active .q-toggle__inner {
            color: #00ff66 !important;
        }
        .q-toggle[aria-checked="true"] .q-toggle__track,
        .q-toggle.q-toggle--active .q-toggle__track {
            background-color: #123f1f !important;
        }

        a, .q-item.q-item--active, .q-item.q-router-link--active {
            color: #00ff66 !important;
        }

        .q-pagination .q-btn--standard,
        .q-pagination .q-btn[aria-current="true"],
        .q-pagination .q-btn.text-primary {
            color: #00ff66 !important;
            border-color: #00ff66 !important;
        }

        .q-linear-progress, .q-circular-progress {
            color: #00ff66 !important;
        }
        </style>
        """
    )


def show_help_dialog():
    with ui.context.client.content:
        with ui.dialog() as dialog:
            with compat_card().classes("w-[360px]"):
                title = IDENTITY.replace("/", " ")
                title = title.split("@")[0] if "@" in title else title
                ui.label(title).classes("text-lg font-bold")
                ui.separator()

                items = {
                    "Documentation": "https://github.com/daya0576/beaverhabits/wiki",
                    "Supporter": "https://www.beaverhabits.com/pricing",
                    "YouTube": "https://www.youtube.com/@beaverhabits",
                    "Bugs & Feature Requests": "https://github.com/daya0576/beaverhabits/issues",
                }

                with ui.grid(columns=2).classes("gap-2"):
                    for name, link in items.items():
                        ui.link(name, link, new_tab=True)

        dialog.props('backdrop-filter="blur(4px)"')
        dialog.open()


@ui.refreshable
def menu_component():
    """Dropdown menu for the top-right corner of the page."""
    with ui.menu().props('role="menu" transition-duration="50"'):
        add_menu()
        separator()

        with menu_icon_item("Tools", auto_close=False).classes("pr-1"):
            with ui.item_section().props("side").classes("pl-[1px]"):
                ui.icon(icons.CHEVRON_RIGHT)
            with ui.menu().props('anchor="top end" self="top start" auto-close'):
                # Stats for all habtis
                menu_icon_item("Reorder", lambda: redirect("order"))
                separator()

                # Export & import
                menu_icon_item("Export", lambda: redirect("export"))
                separator()
                imp = menu_icon_item("Import", lambda: redirect("import"))
                if is_page_demo():
                    imp.classes("disabled")
                separator()

                # Stats for all habtis
                menu_icon_item("Stats", lambda: redirect("stats"))
                separator()

        separator()

        # About page
        menu_icon_item("Help", show_help_dialog)
        separator()

        # Login & Logout
        menu_icon_item("Logout", lambda: user_logout() and ui.navigate.to("/login"))


@contextmanager
def layout(
    title: str | None = None,
    habit: Habit | None = None,
    habit_list: HabitList | None = None,
    page_ui: ui.refreshable | None = None,
):
    # Standard headers
    custom_headers()
    pwa_headers()

    # Center the content on small screens
    with ui.column().classes("mx-auto mx-0"):

        # Layout wrapper
        with ui.row().classes("w-full gap-x-1"):
            title, target = title or page_title(), get_root_path()
            menu_header(title, target=target)
            ui.space()

            if habit:
                edit_dialog = habit_edit_dialog(habit)
                edit_btn = menu_icon_button("sym_r_pen_size_3", tooltip="Edit habit")
                edit_btn.on_click(edit_dialog.open)
            elif habit_list and "add" in page_path():
                with menu_icon_button("sym_o_swap_vert", tooltip="Sort"):
                    sort_menu(habit_list)
            elif "stats" in page_path() and page_ui:
                with menu_icon_button("sym_o_expand_content", tooltip="Date"):
                    stats_date_pick_menu()

            with menu_icon_button("sym_o_menu"):
                menu_component()

        yield
