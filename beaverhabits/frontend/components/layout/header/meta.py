from nicegui import ui

from beaverhabits.configs import settings

def add_meta_tags() -> None:
    """Add meta tags to the page header."""
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
    )
    ui.add_head_html('<meta name="apple-mobile-web-app-title" content="Beaver">')
    ui.add_head_html(
        '<meta name="apple-mobile-web-app-status-bar-style" content="black">'
    )
    ui.add_head_html('<meta name="theme-color" content="#121212">')

    # viewBox="90 90 220 220"
    ui.add_head_html(
        '<link rel="apple-touch-icon" href="/statics/images/apple-touch-icon-v4.png">'
    )

    # Experimental PWA support
    if settings.ENABLE_IOS_STANDALONE:
        ui.add_head_html('<meta name="apple-mobile-web-app-capable" content="yes">')

def add_analytics() -> None:
    """Add analytics scripts to the page header."""
    ui.add_head_html(
        '<script defer src="https://cloud.umami.is/script.js" data-website-id="246fa4ac-0f4f-464a-8a32-14c9f75fed77"></script>'
    )
