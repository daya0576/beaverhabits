"""CSS styles for frontend"""

CALENDAR_CSS = """
.calendar-heatmap {
    display: grid;
    grid-template-columns: repeat(53, 1fr);
    gap: 3px;
}

.calendar-heatmap-day {
    aspect-ratio: 1;
    border-radius: 2px;
}
"""

CHECK_BOX_CSS = """
.checkbox-container {
    display: inline-block;
    width: 56px;  /* w-14 */
}
"""

habit_animations = """
@keyframes countdown {
    from { width: 100%; }
    to { width: 0; }
}

@keyframes highlight {
    0% { border: 2px solid #007bff; }
    100% { border: 2px solid transparent; }
}

.habit-card {
    position: relative;
    transition: transform 0.3s ease-out;
    border: 2px solid transparent;  /* Reserve space for highlight border */
}

.resort-pending::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    height: 2px;
    width: 100%;
    background: #007bff;
    animation: countdown 2s linear;
}

.highlight-card {
    animation: highlight 2s ease-out;
}
"""

EXPANSION_CSS = """
.q-expansion-item__container {
    border: none !important;
}
"""

HIDE_TIMELINE_TITLE = """
.q-timeline__title {
    display: none;
}
"""

__all__ = [
    'CALENDAR_CSS',
    'CHECK_BOX_CSS',
    'EXPANSION_CSS',
    'HIDE_TIMELINE_TITLE',
    'habit_animations',
]
