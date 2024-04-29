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

SQUARE_UNCHECKED = """\
img:data:image/svg+xml;charset=utf8,\
<svg viewBox='0 0 20 20' xmlns='http://www.w3.org/2000/svg'>\
    <rect x='1' y='1' width='18' height='18' rx='2.5' fill='rgb(54,54,54)'/>\
    <text x='10' text-anchor='middle' y='10' dominant-baseline='central' fill='white' font-size='8' \
        style='font-family: Roboto,-apple-system,Helvetica Neue,Helvetica,Arial,sans-serif; font-weight: normal; font-style: normal'\
        class='font-light'\
    >{text}</text>\
</svg>\
"""
# fmt: on
