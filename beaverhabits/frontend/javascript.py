from nicegui import ui

PRESERVE_SCROLL = """\
// Store scroll position in localStorage before refresh
window.addEventListener('beforeunload', () => {
    localStorage.setItem('scrollPos', window.scrollY);
});

// Restore scroll position after refresh
window.addEventListener('load', () => {
    const scrollPos = localStorage.getItem('scrollPos');
    if (scrollPos) {
        window.scrollTo(0, parseInt(scrollPos));
        localStorage.removeItem('scrollPos');
    }
});
"""

PREVENT_CONTEXT_MENU = """\
document.body.style.webkitTouchCallout='none';

document.addEventListener('contextmenu', function(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    return false;
});
"""

UNHOVER_CHECKBOXES = """\
const elements = document.querySelectorAll('.q-checkbox');

elements.forEach(element => {
  const mouseOutEvent = new Event('mouseout');
  element.addEventListener('mouseout', () => {
    element.dispatchEvent(mouseOutEvent);
  });
});
"""


def preserve_scroll():
    ui.run_javascript(PRESERVE_SCROLL)

def prevent_context_menu():
    ui.run_javascript(PREVENT_CONTEXT_MENU)


def unhover_checkboxes():
    ui.run_javascript(UNHOVER_CHECKBOXES)
