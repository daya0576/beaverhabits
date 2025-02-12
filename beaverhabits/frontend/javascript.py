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

update_habit_color = """
window.updateHabitColor = function(habitId, weeklyGoal, weekTicks, isSkippedToday) {
    // Find the habit name element by ID
    const habitElement = document.querySelector(`[href*="/habits/${habitId}"]`);
    if (!habitElement) {
        console.log('Habit element not found:', habitId);
        return;
    }

    // If habit is skipped today, keep it orangered
    if (isSkippedToday) {
        habitElement.style.color = 'orangered';
        return;
    }

    // If weekly goal is met, set to lightgreen, otherwise orangered
    habitElement.style.color = weekTicks >= weeklyGoal ? 'lightgreen' : 'orangered';
    console.log(`Updated color for habit ${habitId}: weeklyGoal=${weeklyGoal}, weekTicks=${weekTicks}, color=${habitElement.style.color}`);
};

// Function to update all habit colors
window.updateAllHabitColors = function() {
    // Find all habit elements
    const habitElements = document.querySelectorAll('[data-habit-id]');
    habitElements.forEach(element => {
        const habitId = element.getAttribute('data-habit-id');
        if (habitId) {
            // Get the current state from the element's style
            const isSkippedToday = element.style.color === 'orangered';
            const weeklyGoal = parseInt(element.getAttribute('data-weekly-goal') || '0');
            const weekTicks = parseInt(element.getAttribute('data-week-ticks') || '0');
            
            // Update the color
            window.updateHabitColor(habitId, weeklyGoal, weekTicks, isSkippedToday);
        }
    });
};

// Update colors when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.updateAllHabitColors();
});
"""

__all__ = [
    'prevent_context_menu',
    'preserve_scroll',
    'update_habit_color',
]
