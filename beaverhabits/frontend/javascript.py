from jinja2 import Environment
from nicegui import __version__ as version
from nicegui import ui

from beaverhabits.configs import settings

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

PADDLE_JS_TEMPLATE = """\
<script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
<script type="text/javascript">
  Paddle.Initialize({ 
    token: '{{paddle_token}}' 
  });
  {% if sandbox %}Paddle.Environment.set("sandbox");{% endif %}

  function getPrices() {
    console.log('start...');
    var request = {
        items: [{ quantity: 1, priceId: '{{price_id}}' }]
    };
    console.log(request);
    Paddle.PricePreview(request)
      .then((result) => {
        console.log(result);
      })
      .catch((error) => {
        console.error(error);
      });
  }

  // open checkout
  // https://developer.paddle.com/build/checkout/build-overlay-checkout
  function openCheckout(email) {
    customer = {}
    if (email) {
      customer.email = email;
    }
    console.log(customer);
    Paddle.Checkout.open({
      items: [{ priceId: "{{price_id}}", quantity: 1 }],
      customer: customer,
      settings: {
        theme: "dark",
      }
    });
  }
</script>
"""

env = Environment()
PADDLE_JS = env.from_string(PADDLE_JS_TEMPLATE).render(
    paddle_token=settings.PADDLE_CLIENT_SIDE_TOKEN,
    sandbox=settings.PADDLE_SANDBOX,
    product_id=settings.PADDLE_PRODUCT_ID,
    price_id=settings.PADDLE_PRICE_ID,
)


def prevent_context_menu():
    ui.run_javascript(PREVENT_CONTEXT_MENU)


def unhover_checkboxes():
    ui.run_javascript(UNHOVER_CHECKBOXES)


def load_cache():
    ui.run_javascript(LOAD_CACHE)
