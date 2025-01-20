from nicegui import ui

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
console.log(elements);

elements.forEach(element => {
  const mouseOutEvent = new Event('mouseout');
  element.addEventListener('mouseout', () => {
    console.log('mouseout');
    element.dispatchEvent(mouseOutEvent);
  });
});
"""


def prevent_context_menu():
    ui.run_javascript(PREVENT_CONTEXT_MENU)


def unhover_checkboxes():
    ui.run_javascript(UNHOVER_CHECKBOXES)
