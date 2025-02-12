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

// Track resort timer and affected cards
let resortTimer = null;
let pendingCards = new Map();  // Map of habitId -> original priority

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

    // Update priority and check if resort needed
    const card = document.querySelector(`.habit-card[data-habit-id="${{habitId}}"]`);
    if (card) {{
        // Calculate new priority (3=no ticks (top), 2=partial ticks, 1=skipped, 0=completed (bottom))
        const newPriority = isSkippedToday ? 1 : (weekTicks >= weeklyGoal ? 0 : (weekTicks > 0 ? 2 : 3));
        const currentPriority = parseInt(card.getAttribute('data-priority'));
        
        // If this is the first change for this habit, store its original priority
        if (!pendingCards.has(habitId)) {{
            pendingCards.set(habitId, currentPriority);
            debugLog(`Storing original priority ${{currentPriority}} for habit ${{habitId}}`);
        }}
        
        // If we're back to original priority, remove from pending
        if (newPriority === pendingCards.get(habitId)) {{
            debugLog(`Habit ${{habitId}} back to original priority ${{newPriority}}, removing pending state`);
            pendingCards.delete(habitId);
            card.classList.remove('resort-pending');
            
            // If no more pending changes, clear timer
            if (pendingCards.size === 0 && resortTimer) {{
                debugLog('No more pending changes, clearing timer');
                clearTimeout(resortTimer);
                resortTimer = null;
            }}
            return;  // No need to continue
        }}
        
        // Update priority attribute
        card.setAttribute('data-priority', newPriority);
        debugLog(`Updated priority to ${{newPriority}}`);
        
        // Add/refresh progress bar
        card.classList.add('resort-pending');
        
        // Clear existing timer
        if (resortTimer) {{
            clearTimeout(resortTimer);
            // Restart progress bars for all pending cards
            pendingCards.forEach((_, id) => {{
                const pendingCard = document.querySelector(`[data-habit-id="${{id}}"]`);
                pendingCard.classList.remove('resort-pending');
                void pendingCard.offsetWidth;  // Force reflow
                pendingCard.classList.add('resort-pending');
            }});
        }}
        
        // Set new timer
        resortTimer = setTimeout(() => {{
            debugLog('Resort timer triggered');
            // Get all pending cards before clearing
            const pendingCardIds = Array.from(pendingCards.keys());
            
            // Remove progress bars
            pendingCards.forEach((_, id) => {{
                const pendingCard = document.querySelector(`[data-habit-id="${{id}}"]`);
                pendingCard.classList.remove('resort-pending');
            }});
            pendingCards.clear();
            
            // Resort with animation
            window.sortHabits();
            
            // Add highlight to only the changed cards
            pendingCardIds.forEach(id => {{
                const card = document.querySelector(`[data-habit-id="${{id}}"]`);
                if (card) {{
                    // Add highlight immediately
                    card.classList.add('highlight-card');
                    
                    // Delay scroll to happen after reordering animation
                    setTimeout(() => {{
                        // Scroll to the card
                        card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        
                        // Remove highlight after scroll animation
                        setTimeout(() => {{
                            card.classList.remove('highlight-card');
                        }}, 1000);  // Remove highlight 1s after scroll starts
                    }}, 300);  // Start scroll 300ms after reordering
                }}
            }});
        }}, 2000);
    }}
}};

// Function to sort habits with animation
window.sortHabits = function() {{
    debugLog('Sorting habits');
    const container = document.querySelector('.habit-card-container');
    if (!container) {{
        console.error('Habit container not found');
        return;
    }}

    const cards = Array.from(container.querySelectorAll('.habit-card'));
    debugLog(`Found ${{cards.length}} cards to sort`);
    
    // Get current positions
    const oldPositions = new Map();
    cards.forEach(card => {{
        const rect = card.getBoundingClientRect();
        oldPositions.set(card, {{ top: rect.top, left: rect.left }});
    }});
    
    // Sort cards
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
    
    // Reorder elements
    debugLog('Reordering elements with animation');
    cards.forEach(card => container.appendChild(card));
    
    // Animate to new positions
    cards.forEach(card => {{
        const oldPos = oldPositions.get(card);
        const newPos = card.getBoundingClientRect();
        
        // Calculate the difference
        const deltaY = oldPos.top - newPos.top;
        const deltaX = oldPos.left - newPos.left;
        
        // Apply the reverse transform to start
        card.style.transform = `translate(${{deltaX}}px, ${{deltaY}}px)`;
        
        // Force reflow
        void card.offsetWidth;
        
        // Remove the transform with transition
        card.style.transform = '';
    }});
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
