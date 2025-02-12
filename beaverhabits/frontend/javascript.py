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
};
"""

__all__ = [
    'prevent_context_menu',
    'preserve_scroll',
    'update_habit_color',
]
