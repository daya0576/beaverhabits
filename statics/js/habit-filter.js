// Use IIFE to avoid global variables
window.HabitFilter = (function() {
    let currentFilter = null;
    let enabled = false;

    function setEnabled(value) {
        enabled = value;
    }

    function filterHabits(letter) {
        // Don't filter if disabled
        if (!enabled) {
            return;
        }

        // Toggle filter if clicking same letter
        if (currentFilter === letter) {
            currentFilter = null;
        } else {
            currentFilter = letter;
        }

        // Update button states
        document.querySelectorAll('.letter-filter-btn').forEach(btn => {
            if (btn.textContent === currentFilter) {
                btn.classList.add('active-filter');
            } else {
                btn.classList.remove('active-filter');
            }
        });

        // Filter cards
        const cards = document.querySelectorAll('.habit-card');
        cards.forEach(card => {
            const name = card.getAttribute('data-name').toUpperCase();
            if (!currentFilter || name.startsWith(currentFilter)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Public API
    return {
        setEnabled: setEnabled,
        filterHabits: filterHabits
    };
})();
