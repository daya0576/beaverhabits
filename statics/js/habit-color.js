window.updateHabitState = function(habitId, state) {
    // Only handle card sorting
    const card = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
    if (card && state.sorting) {
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
        
        // Resort habits
        window.sortHabits();
    }
};
