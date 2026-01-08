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

NOTE_CSS = """
.q-textarea textarea {
  field-sizing: content;
  min-height: 118px;
}

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

TEXTAREA_CSS = """
.textarea-style {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
    line-height: 1.5;
}
"""


WHITE_FLASH_PREVENT = """\
:root {
  --theme-color: #121212;
  --background-color: #f9f9f9;
}
@media (prefers-color-scheme: dark) {
  :root {
    --theme-color: #121212;
    --background-color: #121212;
  }
}

body {
  background-color: var(--background-color);
  color: var(--theme-color);

  user-select: none;
  touch-callout:none;
  -webkit-touch-callout:none;
  -webkit-touch-callout: none;
  -webkit-user-callout: none;
  -webkit-user-select: none;
  -webkit-user-drag: none;
  -webkit-user-modify: none;
  -webkit-highlight: none;
}

.body--light {
  background-color: #f9f9f9;
  color: #121212;
  
  .nicegui-link {
    color: #121212;
  }

  .theme-icon-checkbox .q-checkbox__inner--falsy .q-checkbox__icon {
    color: #BDBDBD;
  }
  .theme-icon-checkbox .q-checkbox__inner--truthy .q-checkbox__icon {
    color: #1976d2;
  }

  .theme-header-date {
    font-size: 85%; 
    font-weight: 500; 
    color: #616161;
  }

  .theme-menu-icon {
    color: #121212;
  }

  .theme-card-shadow {
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
  }
}

.body--dark {
  background-color: #121212;
  color: #fff;

  .nicegui-link {
    color: #FFF;
  }

  .theme-icon-checkbox .q-checkbox__inner--falsy .q-checkbox__icon {
    color: #616161;
  }
  .theme-icon-checkbox .q-checkbox__inner--truthy .q-checkbox__icon {
    color: #6796CF;
  }
  .q-checkbox--dark .q-checkbox__inner--falsy {
    color: hsla(0, 0%, 100%, .5);
  }

  .theme-header-date {
    font-size: 85%; 
    font-weight: 500; 
    color: #9E9E9E;
  }

  .theme-menu-icon {
    color: #FFF;
  }

  .theme-card-shadow {
    box-shadow: none;
  }
}
"""
