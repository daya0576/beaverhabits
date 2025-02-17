# Checkbox styles
CHECK_BOX_CSS = """
.q-checkbox {
    margin: 0;
}
"""

# Expansion styles
EXPANSION_CSS = """
.q-expansion-item__container {
    border: none !important;
}
"""

# Hide timeline title
HIDE_TIMELINE_TITLE = """
.q-timeline__title {
    display: none;
}
"""

# Calendar styles
CALENDAR_CSS = """
.calendar-heatmap {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    border-radius: 3px;
    font-size: 10px;
    position: relative;
    display: inline-block;
    overflow: visible;
}

.calendar-heatmap .label {
    padding: 0 5px;
}

.calendar-heatmap .meta {
    display: flex;
}

.calendar-heatmap .graph-legend {
    flex: 1;
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}

.calendar-heatmap .graph {
    padding: 10px 3px 0 3px;
    position: relative;
    display: inline-block;
    white-space: nowrap;
    overflow: hidden;
}

.calendar-heatmap .graph-label {
    fill: #aaa;
    font-size: 10px;
}

.calendar-heatmap .graph-rect {
    fill: #ebedf0;
    shape-rendering: geometricPrecision;
}

.calendar-heatmap .graph-rect:hover {
    stroke: #000;
    stroke-width: 1px;
}

.calendar-heatmap .is-today .graph-rect {
    stroke: #fff;
    stroke-width: 1px;
}

.calendar-heatmap .is-last-week .graph-rect {
    stroke: #fb4934;
    stroke-width: 1px;
}

.calendar-heatmap .color-empty {
    fill: #ebedf0;
}

.calendar-heatmap .color-filled {
    fill: #7bc96f;
}

.calendar-heatmap .color-filled-skipped {
    fill: #969696;
}

.calendar-heatmap .graph-rect:hover {
    stroke: #000;
    stroke-width: 1px;
}
"""

# Habit animations
habit_animations = """
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

/* Letter filter styles */
.letter-filter-btn {
    min-width: 32px;
    transition: background-color 0.2s;
}
.active-filter {
    background-color: rgba(255, 255, 255, 0.2) !important;
}
"""
