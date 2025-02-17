// Global state to track initialization
window.habitColorState = {
    initialized: false,
    debug: true
};

// Track resort timer and affected cards
let resortTimer = null;
let pendingCards = new Map();  // Map of habitId -> original priority

window.updateHabitColor = function(habitId, weeklyGoal, weekTicks, isSkippedToday, lastWeekComplete) {
    if (!window.habitColorState.initialized) {
        debugLog('Script not initialized yet, initializing now');
        window.habitColorState.initialized = true;
    }
    debugLog(`Updating color for habit ${habitId}`);
    debugLog(`State: weeklyGoal=${weeklyGoal}, weekTicks=${weekTicks}, isSkippedToday=${isSkippedToday}`);
    
    // Find all elements with this habit ID
    const habitElements = document.querySelectorAll(`[data-habit-id="${habitId}"]`);
    debugLog(`Found ${habitElements.length} elements for habit ${habitId}`);
    
    if (habitElements.length === 0) {
        console.error('No habit elements found for id:', habitId);
        return;
    }

    // Determine the new color
    let newColor;
    if (isSkippedToday) {
        debugLog(`Setting skipped color: ${HABIT_SETTINGS.colors.skipped}`);
        newColor = HABIT_SETTINGS.colors.skipped;
    } else if (!lastWeekComplete && weeklyGoal > 0) {
        debugLog(`Setting last week incomplete color: ${HABIT_SETTINGS.colors.last_week_incomplete}`);
        newColor = HABIT_SETTINGS.colors.last_week_incomplete;
    } else {
        newColor = weekTicks >= weeklyGoal ? HABIT_SETTINGS.colors.completed : HABIT_SETTINGS.colors.incomplete;
        debugLog(`Setting color to ${newColor} based on weekTicks=${weekTicks} >= weeklyGoal=${weeklyGoal}`);
    }

    // Update all elements
    habitElements.forEach(element => {
        debugLog('Updating element:', element);
        element.style.color = newColor;
    });

    // Update priority and check if resort needed
    const card = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
    if (card) {
        // Calculate new priority (0=no checks (first), 1=partial (second), 2=skipped (third), 3=completed (last))
        const isCompleted = weeklyGoal > 0 && weekTicks >= weeklyGoal;
        const hasActions = weekTicks > 0 || isSkippedToday;  // Count ticks and skips as actions
        let newPriority;
        
        if (!hasActions) {
            newPriority = 0;  // No checks (first)
        } else if (hasActions && !isSkippedToday && !isCompleted) {
            newPriority = 1;  // Partially checked (second)
        } else if (isSkippedToday) {
            newPriority = 2;  // Skipped today (third)
        } else {
            newPriority = 3;  // Completed (last)
        }
        
        const currentPriority = parseInt(card.getAttribute('data-priority'));
        
        debugLog(`Priority calculation:
            isCompleted: ${isCompleted} (weeklyGoal=${weeklyGoal}, weekTicks=${weekTicks})
            weekTicks > 0: ${weekTicks > 0}
            isSkippedToday: ${isSkippedToday}
            hasActions: ${hasActions}
            Final priority: ${newPriority}
        `);
        
        // If this is the first change for this habit, store its original priority
        if (!pendingCards.has(habitId)) {
            pendingCards.set(habitId, currentPriority);
            debugLog(`Storing original priority ${currentPriority} for habit ${habitId}`);
        }
        
        // If we're back to original priority, remove from pending
        if (newPriority === pendingCards.get(habitId)) {
            debugLog(`Habit ${habitId} back to original priority ${newPriority}, removing pending state`);
            pendingCards.delete(habitId);
            card.classList.remove('resort-pending');
            
            // If no more pending changes, clear timer
            if (pendingCards.size === 0 && resortTimer) {
                debugLog('No more pending changes, clearing timer');
                clearTimeout(resortTimer);
                resortTimer = null;
            }
            return;  // No need to continue
        }
        
        // Update priority attribute and label
        card.setAttribute('data-priority', newPriority);
        const priorityLabel = card.querySelector('.priority-label');
        if (priorityLabel) {
            priorityLabel.textContent = `Priority: ${newPriority}`;
        }
        debugLog(`Updated priority to ${newPriority}`);
        
        // Add/refresh progress bar
        card.classList.add('resort-pending');
        
        // Clear existing timer
        if (resortTimer) {
            clearTimeout(resortTimer);
            // Restart progress bars for all pending cards
            pendingCards.forEach((_, id) => {
                const pendingCard = document.querySelector(`[data-habit-id="${id}"]`);
                pendingCard.classList.remove('resort-pending');
                void pendingCard.offsetWidth;  // Force reflow
                pendingCard.classList.add('resort-pending');
            });
        }
        
        // Set new timer
        resortTimer = setTimeout(() => {
            debugLog('Resort timer triggered');
            // Get all pending cards before clearing
            const pendingCardIds = Array.from(pendingCards.keys());
            
            // Remove progress bars
            pendingCards.forEach((_, id) => {
                const pendingCard = document.querySelector(`[data-habit-id="${id}"]`);
                pendingCard.classList.remove('resort-pending');
            });
            pendingCards.clear();
            
            // Resort with animation
            window.sortHabits();
            
            // Add highlight to only the changed cards
            pendingCardIds.forEach(id => {
                const card = document.querySelector(`[data-habit-id="${id}"]`);
                if (card) {
                    // Add highlight immediately
                    card.classList.add('highlight-card');
                    
                    // Remove highlight after animation
                    setTimeout(() => {
                        card.classList.remove('highlight-card');
                    }, 1000);
                }
            });
        }, 2000);
    }
};

// Function to update all habit colors
window.updateAllHabitColors = function() {
    debugLog('Updating all habit colors');
    // Find all habit elements
    const habitElements = document.querySelectorAll('[data-habit-id]');
    debugLog(`Found ${habitElements.length} habit elements`);
    
    habitElements.forEach(element => {
        const habitId = element.getAttribute('data-habit-id');
        if (habitId) {
            debugLog(`Processing habit: ${habitId}`);
            // Get the skipped state from data attribute
            const isSkippedToday = element.getAttribute('data-skipped') === 'true';
            const weeklyGoal = parseInt(element.getAttribute('data-weekly-goal') || '0');
            const weekTicks = parseInt(element.getAttribute('data-week-ticks') || '0');
            const lastWeekComplete = element.getAttribute('data-last-week-complete') === 'true';
            
            debugLog(`Element data: isSkippedToday=${isSkippedToday}, weeklyGoal=${weeklyGoal}, weekTicks=${weekTicks}, lastWeekComplete=${lastWeekComplete}`);
            
            // Update the color
            window.updateHabitColor(habitId, weeklyGoal, weekTicks, isSkippedToday, lastWeekComplete);
        }
    });
};
