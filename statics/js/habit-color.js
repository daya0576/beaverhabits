// Debug logging
function debugLog(...args) {
    if (window.habitColorState?.debug) {
        console.log('[HabitColor]', ...args);
    }
}

// Global state to track initialization
window.habitColorState = {
    initialized: false,
    debug: true
};

// Track resort timer and affected cards
let resortTimer = null;
let pendingCards = new Map();  // Map of habitId -> original priority

window.updateHabitState = function(habitId, state) {
    if (!window.habitColorState.initialized) {
        debugLog('Script not initialized yet, initializing now');
        window.habitColorState.initialized = true;
    }
    debugLog(`Updating state for habit ${habitId}:`, state);
    
    // Find all elements with this habit ID
    const habitElements = document.querySelectorAll(`[data-habit-id="${habitId}"]`);
    debugLog(`Found ${habitElements.length} elements for habit ${habitId}`);
    
    if (habitElements.length === 0) {
        console.error('No habit elements found for id:', habitId);
        return;
    }

    // Update all elements with the new color
    habitElements.forEach(element => {
        debugLog('Updating element:', element);
        element.style.color = state.color;
        
        // Update checkbox state if it's a checkbox
        if (element.classList.contains('q-checkbox')) {
            try {
                // Convert state to Python's expected value (true/null/false)
                const value = state.state === 'checked' ? true : state.state === 'skipped' ? null : false;
                
                // Let Python handle all updates
                if (element._instance?.exposed?._update_style) {
                    element._instance.exposed._update_style(value);
                    debugLog('Called Python update with value:', value);
                }
            } catch (error) {
                console.error('Error updating checkbox:', error);
            }
        }
    });

    // Update card sorting
    const card = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
    if (card) {
        // If this is the first change for this habit, store its original priority
        const currentPriority = parseInt(card.getAttribute('data-priority'));
        if (!pendingCards.has(habitId)) {
            pendingCards.set(habitId, currentPriority);
            debugLog(`Storing original priority ${currentPriority} for habit ${habitId}`);
        }
        
        // Update sorting attributes
        card.setAttribute('data-starred', state.sorting.starred ? '1' : '0');
        card.setAttribute('data-priority', state.sorting.priority);
        card.setAttribute('data-order', state.sorting.order);
        card.setAttribute('data-name', state.sorting.name);
        
        // Update priority label if it exists
        const priorityLabel = card.querySelector('.priority-label');
        if (priorityLabel) {
            priorityLabel.textContent = `Priority: ${state.sorting.priority}`;
        }
        
        // If we're back to original priority, remove from pending
        if (state.sorting.priority === pendingCards.get(habitId)) {
            debugLog(`Habit ${habitId} back to original priority ${state.sorting.priority}, removing pending state`);
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

// Legacy function for backward compatibility
window.updateHabitColor = function(habitId, weeklyGoal, weekTicks, isSkippedToday, lastWeekComplete) {
    console.warn('updateHabitColor is deprecated, use updateHabitState instead');
    // This function is kept for backward compatibility but should not be used
};

// Function to update all habit colors
window.updateAllHabitColors = function() {
    console.warn('updateAllHabitColors is deprecated, server now handles all state updates');
};
