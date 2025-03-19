from nicegui import __version__ as version
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

elements.forEach(element => {
  const mouseOutEvent = new Event('mouseout');
  element.addEventListener('mouseout', () => {
    element.dispatchEvent(mouseOutEvent);
  });
});
"""

LOAD_CACHE = """\
const scriptUrls = [
  '/_nicegui/{__version__}/components/b0b17893a51343979e2090deee730538/input.js',
  '/_nicegui/{__version__}/components/b0b17893a51343979e2090deee730538/echart.js',
  '/_nicegui/{__version__}/libraries/c3db162d662122eb0e7be8cd04794fac/echarts.min.js',
  '/_nicegui/{__version__}/static/utils/dynamic_properties.js'
];

setTimeout(() => {
    for (let i = 0; i < scriptUrls.length; i++) {
      const script = document.createElement('script'); 
      script.src = scriptUrls[i];                     
      script.async = true;
      document.head.appendChild(script);             
      console.log(`Script loaded: ${scriptUrls[i]}`);
    }
}, 500);
""".replace(
    "{__version__}", version
)


def prevent_context_menu():
    ui.run_javascript(PREVENT_CONTEXT_MENU)


def unhover_checkboxes():
    ui.run_javascript(UNHOVER_CHECKBOXES)


def load_cache():
    ui.run_javascript(LOAD_CACHE)
