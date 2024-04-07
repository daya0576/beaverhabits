SVG_TEMPLATE = "img:data:image/svg+xml;charset=utf8,<svg xmlns='http://www.w3.org/2000/svg' height='{height}' viewBox='0 -960 960 960' width='{height}' fill='{color}'><path d='{data}'/></svg>"

# fmt: off
DONE = SVG_TEMPLATE.format(height="24", color="rgb(103,150,207)", data="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z")
CLOSE = SVG_TEMPLATE.format(height="24", color="rgb(97,97,97)", data="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z")
MENU = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z")
DELETE = SVG_TEMPLATE.format(height="24", color="rgb(97,97,97)", data="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z")
# fmt: on
