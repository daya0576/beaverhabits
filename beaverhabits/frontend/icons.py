import re

# https://editsvgcode.com/
SVG_RAW = "img:data:image/svg+xml;charset=utf8,{content}"
SVG_TEMPLATE = "img:data:image/svg+xml;charset=utf8,<svg xmlns='http://www.w3.org/2000/svg' height='{height}' viewBox='0 -960 960 960' width='{height}' fill='{color}'><path d='{data}'/></svg>"
SVG_FLIP = "img:data:image/svg+xml;charset=utf8,<svg xmlns='http://www.w3.org/2000/svg' height='{height}' viewBox='0 -960 960 960' width='{height}' fill='{color}'><g transform='scale(-1, 1) translate(-960, 0)'><path d='{data}'/></g></svg>"
SVG_OUTLINE = "img:data:image/svg+xml;charset=utf8,<svg xmlns='http://www.w3.org/2000/svg' height='24' viewBox='0 -960 960 960' width='24'><path d='{content}' fill='{o_color}' stroke='{o_color}' stroke-width='{o_width}'/><path d='{content}' fill='{i_color}' stroke='{i_color}' stroke-width='{i_width}'/></svg>"

PRIMARY_COLOR = "rgb(103,150,207)"
CLOSE_COLOR = "rgb(97,97,97)"
card_bg_color = "rgb(29,29,29)"
unchecked_square_color = "rgb(54,54,54)"

PATTERN = re.compile(r"rgb\(\d+,\d+,\d+(?:,\d+)?\)")


def fade(color: str, alpha: float):
    m = PATTERN.match(color)
    if not m:
        raise ValueError(f"Invalid color format: {color}")

    r, g, b = map(int, m.group(0)[4:-1].split(","))
    return f"rgba({r*alpha}, {g*alpha}, {b*alpha})"


# fmt: off
DONE = SVG_TEMPLATE.format(height="24", color=PRIMARY_COLOR, data="M382-240 154-468l57-57 171 171 367-367 57 57-424 424Z")
DONE_OUTLINE = SVG_TEMPLATE.format(height="24", color="rgb(103,150,207,0.75)", data="m395-285 339-339-50-51-289 288-119-118-50 50 169 170Zm1 102L124-455l152-152 119 118 289-288 153 153-441 441Z")
DONE_ALL = SVG_TEMPLATE.format(height="24", color=PRIMARY_COLOR, data="M268-240 42-466l57-56 170 170 56 56-57 56Zm226 0L268-466l56-57 170 170 368-368 56 57-424 424Zm0-226-57-56 198-198 57 56-198 198Z")

CLOSE = SVG_TEMPLATE.format(height="24", color="rgb(97,97,97)", data="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z")
SKIP = SVG_TEMPLATE.format(height="24", color="rgb(97,97,97)", data="M240-440v-80h480v80H240Z")

MENU = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M120-240v-80h720v80H120Zm0-200v-80h720v80H120Zm0-200v-80h720v80H120Z")
ADD = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M440-440H240q-17 0-28.5-11.5T200-480q0-17 11.5-28.5T240-520h200v-200q0-17 11.5-28.5T480-760q17 0 28.5 11.5T520-720v200h200q17 0 28.5 11.5T760-480q0 17-11.5 28.5T720-440H520v200q0 17-11.5 28.5T480-200q-17 0-28.5-11.5T440-240v-200Z")

DELETE = SVG_TEMPLATE.format(height="24", color="rgb(158,158,158)", data="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z")
DELETE_F = SVG_TEMPLATE.format(height="24", color="rgb(158,158,158)", data="m376-300 104-104 104 104 56-56-104-104 104-104-56-56-104 104-104-104-56 56 104 104-104 104 56 56Zm-96 180q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520Zm-400 0v520-520Z")
EDIT = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M216-216h51l375-375-51-51-375 375v51Zm-72 72v-153l498-498q11-11 23.84-16 12.83-5 27-5 14.16 0 27.16 5t24 16l51 51q11 11 16 24t5 26.54q0 14.45-5.02 27.54T795-642L297-144H144Zm600-549-51-51 51 51Zm-127.95 76.95L591-642l51 51-25.95-25.05Z")
MORE = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M479.79-192Q450-192 429-213.21t-21-51Q408-294 429.21-315t51-21Q510-336 531-314.79t21 51Q552-234 530.79-213t-51 21Zm0-216Q450-408 429-429.21t-21-51Q408-510 429.21-531t51-21Q510-552 531-530.79t21 51Q552-450 530.79-429t-51 21Zm0-216Q450-624 429-645.21t-21-51Q408-726 429.21-747t51-21Q510-768 531-746.79t21 51Q552-666 530.79-645t-51 21Z")
ARCHIVE = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="m480-276 144-144-51-51-57 57v-150h-72v150l-57-57-51 51 144 144ZM216-624v408h528v-408H216Zm0 480q-29.7 0-50.85-21.15Q144-186.3 144-216v-474q0-14 5.25-27T165-741l54-54q11-11 23.94-16 12.94-5 27.06-5h420q14.12 0 27.06 5T741-795l54 54q10.5 11 15.75 24t5.25 27v474q0 29.7-21.15 50.85Q773.7-144 744-144H216Zm6-552h516l-48-48H270l-48 48Zm258 276Z")

DOWNLOAD = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="M480-320 280-520l56-58 104 104v-326h80v326l104-104 56 58-200 200ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z")
BACKUP = SVG_TEMPLATE.format(height="24", color="rgb(255,255,255)", data="m612-292 56-56-148-148v-184h-80v216l172 172ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm0-400Zm0 320q133 0 226.5-93.5T800-480q0-133-93.5-226.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160Z")

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

# SVG
GITHUB = """\
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
"""
LOGIN = """\
<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e8eaed"><path d="M480-120v-80h280v-560H480v-80h280q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H480Zm-80-160-55-58 102-102H120v-80h327L345-622l55-58 200 200-200 200Z"/></svg>
"""
# fmt: on
