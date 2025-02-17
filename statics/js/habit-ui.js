function scrollToHabit(habitId) {
    setTimeout(() => {
        const cards = document.querySelectorAll(`[data-habit-id="${habitId}"]`);
        const card = cards[cards.length - 1];
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add highlight effect
            card.classList.add('highlight-card');
            setTimeout(() => {
                card.classList.remove('highlight-card');
            }, 1000);
        }
    }, 300);
}

function updateHabitAttributes(habitId, weeklyGoal, weekTicks, isSkippedToday, lastWeekComplete) {
    if (!window.habitColorState) {
        console.error('Habit color state not initialized - check script loading');
        return;
    }

    debugLog('Updating habit:', {
        habitId,
        weeklyGoal,
        weekTicks,
        isSkippedToday
    });

    try {
        // Update all elements with this habit ID
        const habitElements = document.querySelectorAll(`[data-habit-id="${habitId}"]`);
        debugLog(`Found ${habitElements.length} elements for habit ${habitId}`);
        
        habitElements.forEach(element => {
            debugLog('Updating element:', element);
            element.setAttribute('data-weekly-goal', weeklyGoal);
            element.setAttribute('data-week-ticks', weekTicks);
            element.setAttribute('data-skipped', isSkippedToday);
            element.setAttribute('data-last-week-complete', lastWeekComplete);
        });
        
        // Call updateHabitColor to update the colors
        if (window.updateHabitColor) {
            debugLog('Calling updateHabitColor');
            window.updateHabitColor(
                habitId, 
                weeklyGoal,
                weekTicks,
                isSkippedToday,
                lastWeekComplete
            );
        } else {
            console.error('updateHabitColor function not found - check script loading');
        }
    } catch (error) {
        console.error('Error updating habit color:', error);
    }
}
