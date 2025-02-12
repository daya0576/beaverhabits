// Function to sort habits with animation
window.sortHabits = function() {
    debugLog('Sorting habits');
    const container = document.querySelector('.habit-card-container');
    if (!container) {
        console.error('Habit container not found');
        return;
    }

    const cards = Array.from(container.querySelectorAll('.habit-card'));
    debugLog(`Found ${cards.length} cards to sort`);
    
    // Get current positions
    const oldPositions = new Map();
    cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        oldPositions.set(card, { top: rect.top, left: rect.left });
    });
    
    // Sort cards
    cards.sort((a, b) => {
        // First by status
        const statusA = a.getAttribute('data-status');
        const statusB = b.getAttribute('data-status');
        debugLog(`Comparing status: ${a.getAttribute('data-name')}=${statusA} vs ${b.getAttribute('data-name')}=${statusB}`);
        if (statusA !== statusB) return statusA.localeCompare(statusB);
        
        // Then by priority (0=no checks (first), 1=partial (second), 2=skipped (third), 3=completed (last))
        const priorityA = parseInt(a.getAttribute('data-priority'));
        const priorityB = parseInt(b.getAttribute('data-priority'));
        debugLog(`Comparing priorities: ${a.getAttribute('data-name')}=${priorityA} vs ${b.getAttribute('data-name')}=${priorityB}`);
        if (priorityA !== priorityB) return priorityA - priorityB;  // Lower priority first
        
        // Then by star status
        const starredA = parseInt(a.getAttribute('data-starred'));
        const starredB = parseInt(b.getAttribute('data-starred'));
        debugLog(`Comparing stars: ${a.getAttribute('data-name')}=${starredA} vs ${b.getAttribute('data-name')}=${starredB}`);
        if (starredA !== starredB) return starredB - starredA;  // Starred on top
        
        // Then by name
        const nameA = a.getAttribute('data-name').toLowerCase();
        const nameB = b.getAttribute('data-name').toLowerCase();
        const nameDiff = nameA.localeCompare(nameB);
        debugLog(`Comparing names: ${nameA} vs ${nameB} = ${nameDiff}`);
        if (nameDiff !== 0) return nameDiff;
        
        // Finally by manual order
        const orderA = parseInt(a.getAttribute('data-order') || 'Infinity');
        const orderB = parseInt(b.getAttribute('data-order') || 'Infinity');
        debugLog(`Comparing order: ${a.getAttribute('data-name')}=${orderA} vs ${b.getAttribute('data-name')}=${orderB}`);
        return orderA - orderB;
    });
    
    // Reorder elements
    debugLog('Reordering elements with animation');
    cards.forEach(card => container.appendChild(card));
    
    // Animate to new positions
    cards.forEach(card => {
        const oldPos = oldPositions.get(card);
        const newPos = card.getBoundingClientRect();
        
        // Calculate the difference
        const deltaY = oldPos.top - newPos.top;
        const deltaX = oldPos.left - newPos.left;
        
        // Apply the reverse transform to start
        card.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        
        // Force reflow
        void card.offsetWidth;
        
        // Remove the transform with transition
        card.style.transform = '';
    });
};
