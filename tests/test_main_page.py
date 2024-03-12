from nicegui.testing import Screen

from beaverhabits.main import main_page


def test_markdown_message(screen: Screen) -> None:
    main_page()

    screen.open("/")
    screen.should_contain("Try running")
