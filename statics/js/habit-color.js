// Icons
const icons = {
    DONE: '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z" fill="currentColor"/></svg>',
    CLOSE: '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/></svg>'
};

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
            debugLog('Updating checkbox state:', {
                element,
                state: state.state,
                color: state.color,
                hasVModel: !!element._vModel,
                currentValue: element._vModel?.value,
                currentSkipped: element._vModel?.skipped
            });
            
            if (element._vModel) {
                // Update based on explicit state
                element._vModel.value = state.state === 'checked' || state.state === 'skipped';
                element._vModel.skipped = state.state === 'skipped';
                debugLog('Updated vModel:', {
                    newValue: element._vModel.value,
                    newSkipped: element._vModel.skipped,
                    state: state.state
                });
                
                try {
                    // Update icons based on state
                    if (element._vModel.skipped) {
                        element.props(`checked-icon="${icons.CLOSE}" unchecked-icon="${icons.CLOSE}" keep-color`);
                    } else if (element._vModel.value) {
                        element.props(`checked-icon="${icons.DONE}" unchecked-icon="${icons.DONE}" keep-color`);
                    } else {
                        const text_color = element.day === new Date().toISOString().split('T')[0] ? "chartreuse" : "grey";
                        const unchecked_icon = `<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24"><rect fill="rgb(54,54,54)" height="18" width="18" x="3" y="3"/><text x="12" y="15" fill="${text_color}" text-anchor="middle" style="font-size: 12px">${element.day.split('-')[2]}</text></svg>`;
                        element.props(`checked-icon="${unchecked_icon}" unchecked-icon="${unchecked_icon}" keep-color`);
                    }
                    
                    element._update();
                    debugLog('Called _update() successfully');
                } catch (error) {
                    console.error('Error updating checkbox:', error);
                }
            } else {
                console.error('Checkbox missing _vModel:', element);
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
