window.showProgressbar = function(habitId) {
    const card = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
    if (!card) return;
    
    const existingBar = card.querySelector('.progress-bar-animation');
    if (existingBar) {
        existingBar.remove();
    }
    
    // Set card to relative positioning if not already
    if (card.style.position !== 'relative') {
        card.style.position = 'relative';
    }
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar-animation';
    card.appendChild(progressBar);
    
    setTimeout(() => {
        emitEvent('progress_complete_' + habitId, { habitId: habitId });
        progressBar.remove();
    }, 3000);
};
