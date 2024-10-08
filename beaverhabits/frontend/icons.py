# https://editsvgcode.com/
SVG_TEMPLATE = "img:data:image/svg+xml;charset=utf8,<svg xmlns='http://www.w3.org/2000/svg' height='{height}' viewBox='0 -960 960 960' width='{height}' fill='{color}'><path d='{data}'/></svg>"

current_color = "rgb(103,150,207)"
card_bg_color = "rgb(29,29,29)"
unchecked_square_color = "rgb(54,54,54)"

# fmt: off
DONE = SVG_TEMPLATE.format(height="24", color="rgb(103,150,207)", data="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z")
CLOSE = SVG_TEMPLATE.format(height="24", color="rgb(97,97,97)", data="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z")
MENU = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z")
DELETE = SVG_TEMPLATE.format(height="24", color="rgb(158,158,158)", data="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z")

STAR = SVG_TEMPLATE.format(height="24", color="rgb(158,158,158)", data="m305-704 112-145q12-16 28.5-23.5T480-880q18 0 34.5 7.5T543-849l112 145 170 57q26 8 41 29.5t15 47.5q0 12-3.5 24T866-523L756-367l4 164q1 35-23 59t-56 24q-2 0-22-3l-179-50-179 50q-5 2-11 2.5t-11 .5q-32 0-56-24t-23-59l4-165L95-523q-8-11-11.5-23T80-570q0-25 14.5-46.5T135-647l170-57Zm49 69-194 64 124 179-4 191 200-55 200 56-4-192 124-177-194-66-126-165-126 165Zm126 135Z")
STAR_FULL = SVG_TEMPLATE.format(height="24", color="rgb(158,158,158)", data="m305-704 112-145q12-16 28.5-23.5T480-880q18 0 34.5 7.5T543-849l112 145 170 57q26 8 41 29.5t15 47.5q0 12-3.5 24T866-523L756-367l4 164q1 35-23 59t-56 24q-2 0-22-3l-179-50-179 50q-5 2-11 2.5t-11 .5q-32 0-56-24t-23-59l4-165L95-523q-8-11-11.5-23T80-570q0-25 14.5-46.5T135-647l170-57Z")

SQUARE_TODAY_CIRCLE = "<circle cx='10' cy='10' r='7' fill='none' stroke='white' stroke-width='0.5' opacity='0.3'/>"
SQUARE = """\
img:data:image/svg+xml;charset=utf8,\
<svg viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'>\
    <rect x='1' y='1' width='18' height='18' rx='2.5' fill='{color}'/>\
    <text x='10' text-anchor='middle' y='10' dominant-baseline='central' fill='white' font-size='8' \
        style='font-family: Roboto,-apple-system,Helvetica Neue,Helvetica,Arial,sans-serif;'\
        class='font-light'\
    >{text}</text>\
</svg>\
"""

HELP = SVG_TEMPLATE.format(height="24", color="rgb(204,204,204)", data="M478-240q21 0 35.5-14.5T528-290q0-21-14.5-35.5T478-340q-21 0-35.5 14.5T428-290q0 21 14.5 35.5T478-240Zm-36-154h74q0-33 7.5-52t42.5-52q26-26 41-49.5t15-56.5q0-56-41-86t-97-30q-57 0-92.5 30T342-618l66 26q5-18 22.5-39t53.5-21q32 0 48 17.5t16 38.5q0 20-12 37.5T506-526q-44 39-54 59t-10 73Zm38 314q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-80q134 0 227-93t93-227q0-134-93-227t-227-93q-134 0-227 93t-93 227q0 134 93 227t227 93Zm0-320Z")
# fmt: on
