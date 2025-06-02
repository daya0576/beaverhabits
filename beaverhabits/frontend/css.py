# Solve the problem of the checkbox hover effect hide by other checkboxes
# https://github.com/zauberzeug/nicegui/blob/b4bc24bae3d965e0b58e21d9026ec66ba28ae64d/nicegui/static/quasar.css#L1087

CHECK_BOX_CSS = """
body.desktop .q-checkbox--dense:not(.disabled):hover {
    z-index: 10;
}
body.desktop .q-checkbox--dense:not(.disabled):focus .q-checkbox__inner:before, body.desktop .q-checkbox--dense:not(.disabled):hover .q-checkbox__inner:before {
  transform: scale3d(1.4, 1.4, 1);
}

.q-icon img {
    // transition: opacity 0.3s ease;
}
.q-icon img:hover {
    // opacity: 0.5;
}
"""
CALENDAR_CSS = """
.q-date {
    width: 100%;
}
.q-date__calendar, .q-date__actions {
    padding: 0;
}
.q-date__calendar {
    min-height: 0;
}
"""
EXPANSION_CSS = """
.q-item__section--side {
    min-width: 0 !important;
}
"""

HIDE_TIMELINE_TITLE = """\
.q-timeline__title {
    display: none;
}
"""

MARKDOWN_CSS = """
.q-timeline .q-timeline__content {
    white-space: break-spaces;
}
"""

YOUTUBE_CSS = """
.videowrapper {
    float: none;
    clear: both;
    width: 100%;
    position: relative;
    padding-bottom: 56.25%;
    padding-top: 25px;
    height: 0;
}
.videowrapper iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}
"""

WHITE_FLASH_PREVENT = """\
:root {
  --theme-color: #121212;
  --background-color: #121212;
  --link-color: #fff;
  
  --icon-close-color: #616161;
}

@media (prefers-color-scheme: light) {
  :root {
    --theme-color: #EDEDED;
    --background-color: #EDEDED;
    --link-color: #000;
    
    --icon-close-color: #9E9E9E;
  }
}

body {
  background-color: var(--background-color);
  color: var(--theme-color);
}
"""

THEME_COLOR_CSS = """\
.nicegui-link {
  color: var(--link-color);
}

.theme-icon-close {
  fill: #eee;
}
"""
