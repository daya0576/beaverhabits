"""JavaScript code for frontend"""

prevent_context_menu = """
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
});
"""

preserve_scroll = """
// Store scroll position before page refresh
window.addEventListener('beforeunload', function() {
    localStorage.setItem('scrollPosition', window.scrollY);
});

// Restore scroll position after page load
window.addEventListener('load', function() {
    const scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        localStorage.removeItem('scrollPosition');
    }
});
"""

from beaverhabits.configs import settings

update_habit_color = f"""
// Global state to track initialization
window.habitColorState = {{
    initialized: false,
    debug: true
}};

// Debug logging function
function debugLog(...args) {{
    if (window.habitColorState.debug) {{
        console.log('[Habit Color]', ...args);
    }}
}}

debugLog('Initializing habit color update script');

window.updateHabitColor = function(habitId, weeklyGoal, weekTicks, isSkippedToday) {{
    if (!window.habitColorState.initialized) {{
        debugLog('Script not initialized yet, initializing now');
        window.habitColorState.initialized = true;
    }}
    debugLog(`Updating color for habit ${{habitId}}`);
    debugLog(`Parameters: weeklyGoal=${{weeklyGoal}}, weekTicks=${{weekTicks}}, isSkippedToday=${{isSkippedToday}}`);
    
    // Find all elements with this habit ID
    const habitElements = document.querySelectorAll(`[data-habit-id="${{habitId}}"]`);
    debugLog(`Found ${{habitElements.length}} elements for habit ${{habitId}}`);
    
    if (habitElements.length === 0) {{
        console.error('No habit elements found for id:', habitId);
        return;
    }}

    // Determine the new color
    let newColor;
    if (isSkippedToday) {{
        debugLog(`Setting skipped color: {settings.HABIT_COLOR_SKIPPED}`);
        newColor = '{settings.HABIT_COLOR_SKIPPED}';
    }} else {{
        newColor = weekTicks >= weeklyGoal ? '{settings.HABIT_COLOR_COMPLETED}' : '{settings.HABIT_COLOR_INCOMPLETE}';
        debugLog(`Setting color to ${{newColor}} based on weekTicks=${{weekTicks}} >= weeklyGoal=${{weeklyGoal}}`);
    }}

    // Update all elements
    habitElements.forEach(element => {{
        debugLog('Updating element:', element);
        element.style.color = newColor;
    }});

    // Update priority and resort
    const card = document.querySelector(`.habit-card[data-habit-id="${{habitId}}"]`);
    if (card) {{
        // Calculate new priority (3=no ticks (top), 2=partial ticks, 1=skipped, 0=completed (bottom))
        const priority = isSkippedToday ? 1 : (weekTicks >= weeklyGoal ? 0 : (weekTicks > 0 ? 2 : 3));
        card.setAttribute('data-priority', priority);
        debugLog(`Updated priority to ${{priority}}`);
        
        // Resort the list
        window.sortHabits();
    }}
}};

// Function to sort habits
window.sortHabits = function() {{
    debugLog('Sorting habits');
    const container = document.querySelector('.habit-card-container');
    if (!container) {{
        console.error('Habit container not found');
        return;
    }}

    const cards = Array.from(container.querySelectorAll('.habit-card'));
    debugLog(`Found ${{cards.length}} cards to sort`);
    
    cards.sort((a, b) => {{
        // Sort by priority first (3=no ticks (top), 2=partial ticks, 1=skipped, 0=completed (bottom))
        const priorityA = parseInt(a.getAttribute('data-priority'));
        const priorityB = parseInt(b.getAttribute('data-priority'));
        if (priorityA !== priorityB) return priorityB - priorityA;
        
        // Then by star status
        const starredA = parseInt(a.getAttribute('data-starred'));
        const starredB = parseInt(b.getAttribute('data-starred'));
        if (starredA !== starredB) return starredB - starredA;
        
        // Finally by name
        const nameA = a.getAttribute('data-name').toLowerCase();
        const nameB = b.getAttribute('data-name').toLowerCase();
        return nameA.localeCompare(nameB);
    }});
    
    debugLog('Reordering elements');
    cards.forEach(card => container.appendChild(card));
}};

// Function to update all habit colors
window.updateAllHabitColors = function() {{
    debugLog('Updating all habit colors');
    // Find all habit elements
    const habitElements = document.querySelectorAll('[data-habit-id]');
    debugLog(`Found ${{habitElements.length}} habit elements`);
    
    habitElements.forEach(element => {{
        const habitId = element.getAttribute('data-habit-id');
        if (habitId) {{
            debugLog(`Processing habit: ${{habitId}}`);
            // Get the skipped state from data attribute
            const isSkippedToday = element.getAttribute('data-skipped') === 'true';
            const weeklyGoal = parseInt(element.getAttribute('data-weekly-goal') || '0');
            const weekTicks = parseInt(element.getAttribute('data-week-ticks') || '0');
            
            debugLog(`Element data: isSkippedToday=${{isSkippedToday}}, weeklyGoal=${{weeklyGoal}}, weekTicks=${{weekTicks}}`);
            
            // Update the color
            window.updateHabitColor(habitId, weeklyGoal, weekTicks, isSkippedToday);
        }}
    }});
}};

// Initialize when the page loads
debugLog('Setting up load event listener');
window.addEventListener('load', function() {{
    debugLog('Page loaded, initializing');
    if (window.updateAllHabitColors) {{
        debugLog('Calling updateAllHabitColors');
        window.updateAllHabitColors();
    }} else {{
        console.error('updateAllHabitColors not found');
    }}
    
    if (window.sortHabits) {{
        debugLog('Calling initial sort');
        window.sortHabits();
    }} else {{
        console.error('sortHabits not found');
    }}
}});
"""

__all__ = [
    'prevent_context_menu',
    'preserve_scroll',
    'update_habit_color',
]
