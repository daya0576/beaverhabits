from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import css

def add_settings_script() -> None:
    """Add settings as JavaScript variables."""
    ui.add_head_html(f'''
        <script>
        window.HABIT_SETTINGS = {{
            colors: {{
                skipped: "{settings.HABIT_COLOR_SKIPPED}",
                completed: "{settings.HABIT_COLOR_COMPLETED}",
                incomplete: "{settings.HABIT_COLOR_INCOMPLETE}",
                last_week_incomplete: "{settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE}"
            }}
        }};
        </script>
    ''')

def add_javascript_files() -> None:
    """Add JavaScript files to the page."""
    # Add utils first as other scripts may depend on it
    ui.add_head_html('<script src="/statics/js/utils.js"></script>')
    
    # Add settings before other scripts that use it
    ui.add_head_html('<script src="/statics/js/settings.js"></script>')
    
    # Add core habit scripts in dependency order
    ui.add_head_html('<script src="/statics/js/habit-color.js"></script>')
    ui.add_head_html('<script src="/statics/js/habit-sort.js"></script>')
    ui.add_head_html('<script src="/statics/js/habit-ui.js"></script>')
    
    # Add filter script last as it depends on other scripts
    ui.add_head_html('<script src="/statics/js/habit-filter.js"></script>')

def add_css_styles() -> None:
    """Add CSS styles to the page."""
    # Add CSS for animations
    ui.add_head_html(f'<style>{css.habit_animations}</style>')
    
    # Add CSS for transitions
    ui.add_head_html('''
        <style>
        .habit-card {
            transition: transform 0.3s ease-out;
        }
        .resort-pending {
            position: relative;
        }
        .resort-pending::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: #4CAF50;
            animation: progress 2s linear;
        }
        @keyframes progress {
            0% { width: 100%; }
            100% { width: 0%; }
        }
        .highlight-card {
            animation: highlight 1s ease-out;
        }
        @keyframes highlight {
            0% { background-color: rgba(76, 175, 80, 0.2); }
            100% { background-color: transparent; }
        }
        </style>
    ''')

def add_all_scripts() -> None:
    """Add all scripts and styles to the page."""
    add_settings_script()
    add_javascript_files()
    add_css_styles()
