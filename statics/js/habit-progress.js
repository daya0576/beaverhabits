window.showProgressbar = function(habitId) {
    const card = document.querySelector(`.habit-card[data-habit-id="${habitId}"]`);
    if (!card) return;
    
    const existingBar = card.querySelector('.progress-bar');
    if (existingBar) {
        existingBar.remove();
    }
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    card.appendChild(progressBar);
    
    setTimeout(() => {
        emitEvent('progress_complete_' + habitId, { habitId: habitId });
        progressBar.remove();
    }, 3000);
};
