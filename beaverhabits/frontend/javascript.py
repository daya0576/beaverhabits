from nicegui import ui

PRESERVE_SCROLL = """\
// Store scroll position in localStorage before refresh
window.addEventListener('beforeunload', () => {
    localStorage.setItem('scrollPos', window.scrollY);
});

// Restore scroll position after refresh
window.addEventListener('load', () => {
    const scrollPos = localStorage.getItem('scrollPos');
    if (scrollPos) {
        window.scrollTo(0, parseInt(scrollPos));
        localStorage.removeItem('scrollPos');
    }
});
"""

PREVENT_CONTEXT_MENU = """\
document.body.style.webkitTouchCallout='none';

document.addEventListener('contextmenu', function(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    return false;
});
"""

UNHOVER_CHECKBOXES = """\
const elements = document.querySelectorAll('.q-checkbox');

elements.forEach(element => {
  const mouseOutEvent = new Event('mouseout');
  element.addEventListener('mouseout', () => {
    element.dispatchEvent(mouseOutEvent);
  });
});
"""


def preserve_scroll():
    ui.run_javascript(PRESERVE_SCROLL)

def prevent_context_menu():
    ui.run_javascript(PREVENT_CONTEXT_MENU)


def unhover_checkboxes():
    ui.run_javascript(UNHOVER_CHECKBOXES)

UPDATE_HABIT_COLOR = """\
if (!window.updateHabitColor) {
    // Add styles for reordering animation
    const style = document.createElement('style');
    style.textContent = `
    .habit-card-container {
        width: 100%;
        max-width: 600px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 8px;
    }
    .habit-card {
        transition: all 1.5s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        width: 100%;
        min-width: 0;
        box-sizing: border-box;
        transform-origin: center;
    }
    .habit-card.reordering {
        border-color: rgba(0, 0, 255, 0.15);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: scale(1.01);
    }
    `;
    document.head.appendChild(style);

    window.updateHabitColor = function(habitId, weeklyGoal, currentWeekTicks, isSkippedToday) {
        console.log('updateHabitColor:', { habitId, weeklyGoal, currentWeekTicks, isSkippedToday });
        
        const habitLink = document.querySelector(`[data-habit-id="${habitId}"]`);
        if (!habitLink) {
            console.warn('Habit link not found:', habitId);
            return;
        }
        
        let newColor;
        // Show gray if skipped today
        if (isSkippedToday === true) {  // Explicit check for true
            newColor = 'gray';
            console.log('Setting color to gray (skipped)');
        } else {
            // Update color based on weekly goal
            if (!weeklyGoal || currentWeekTicks >= weeklyGoal) {
                newColor = 'lightgreen';
                console.log('Setting color to lightgreen (goal met)');
            } else {
                newColor = 'orangered';
                console.log('Setting color to orangered (goal not met)');
            }
        }
        
        console.log(`Updating color for habit ${habitId} from ${habitLink.style.color} to ${newColor}`);
        habitLink.style.color = newColor;
        
        // Update priority and trigger reordering
        const habitCard = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
        if (!habitCard) {
            console.warn('Habit card not found:', habitId);
            return;
        }
        
        // Calculate new priority
        let priority = 0;
        if (currentWeekTicks > 0) priority = 1;  // Has some checkmarks
        if (isSkippedToday === true) priority = 2;  // Skipped today
        if (weeklyGoal && currentWeekTicks >= weeklyGoal) priority = 3;  // Completed
        
        console.log('Setting priority:', priority, 'for habit:', habitId);
        
        // Update priority data attribute
        habitCard.setAttribute('data-priority', priority);
        
        // Trigger reordering
        window.reorderHabits();
    };

    window.reorderHabits = function() {
        const firstCard = document.querySelector('.habit-card');
        if (!firstCard) {
            console.warn('No habit cards found');
            return;
        }
        
        const container = firstCard.parentElement;
        const cards = Array.from(container.querySelectorAll('.habit-card'));
        
        console.log('Found cards:', cards.length);
        
        // Sort cards by priority, star status, and name
        cards.sort((a, b) => {
            console.log('Comparing cards:', 
                'A:', a.getAttribute('data-name'), 
                'priority:', a.getAttribute('data-priority'),
                'B:', b.getAttribute('data-name'), 
                'priority:', b.getAttribute('data-priority')
            );
            const aPriority = parseInt(a.getAttribute('data-priority'));
            const bPriority = parseInt(b.getAttribute('data-priority'));
            if (aPriority !== bPriority) return aPriority - bPriority;
            
            const aStarred = parseInt(a.getAttribute('data-starred'));
            const bStarred = parseInt(b.getAttribute('data-starred'));
            if (aStarred !== bStarred) return bStarred - aStarred;  // Higher starred value first
            
            const aName = a.getAttribute('data-name').toLowerCase();
            const bName = b.getAttribute('data-name').toLowerCase();
            return aName.localeCompare(bName);
        });
        
        // Set up container
        container.classList.add('habit-card-container');
        
        // Add reordering class and set order with staggered animation
        cards.forEach((card, index) => {
            // Delay adding reordering class to create cascade effect
            setTimeout(() => {
                card.classList.add('reordering');
            }, index * 150);  // 150ms delay between each card
            
            // Set order immediately
            card.style.order = index;
            
            // Remove reordering class after animation
            setTimeout(() => {
                card.classList.remove('reordering');
            }, 1500 + (index * 150));  // Wait for transition + cascade delay
        });
    };
}
"""

def update_habit_color():
    ui.run_javascript(UPDATE_HABIT_COLOR)
