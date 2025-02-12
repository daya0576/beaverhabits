// Debug logging function
function debugLog(...args) {
    if (window.HABIT_SETTINGS.debug) {
        console.log('[Habit Color]', ...args);
    }
}

// Initialize settings
debugLog('Loading habit settings:', window.HABIT_SETTINGS);
