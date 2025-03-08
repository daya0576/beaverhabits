from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import css

def add_settings_script() -> None:
    """Add settings as JavaScript variables."""
    ui.add_head_html(f'''
        <script>
        window.HABIT_SETTINGS = {{
            colors: {{
                skipped: "{settings.HABIT_COLOR_SKIPPED}",
                completed: "{settings.HABIT_COLOR_COMPLETED}",
                incomplete: "{settings.HABIT_COLOR_INCOMPLETE}",
                last_week_incomplete: "{settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE}"
            }}
        }};
        </script>
    ''')

def add_javascript_files() -> None:
    """Add JavaScript files to the page."""
    # Add utils first as other scripts may depend on it
    ui.add_head_html('<script src="/statics/js/utils.js"></script>')
    
    # Add settings before other scripts that use it
    ui.add_head_html('<script src="/statics/js/settings.js"></script>')
    
    # Add core habit scripts in dependency order
    ui.add_head_html('<script src="/statics/js/habit-color.js"></script>')
    ui.add_head_html('<script src="/statics/js/habit-sort.js"></script>')
    ui.add_head_html('<script src="/statics/js/habit-ui.js"></script>')
    ui.add_head_html('<script src="/statics/js/habit-progress.js"></script>')
    
    # Add filter script last as it depends on other scripts
    ui.add_head_html('<script src="/statics/js/habit-filter.js"></script>')
    
    # Add connection status monitoring script
    ui.add_head_html('''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Create connection status banner if it doesn't exist
        if (!document.getElementById('connection-status-banner')) {
            const banner = document.createElement('div');
            banner.id = 'connection-status-banner';
            banner.textContent = 'Connection lost. Waiting to reconnect...';
            document.body.appendChild(banner);
        }
        
        // Variables to track connection state
        let isConnected = true;
        let lastReconnectTime = 0;
        let disconnectCount = 0;
        let isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const connectionBanner = document.getElementById('connection-status-banner');
        const RECONNECT_DEBOUNCE_TIME = 10000; // 10 seconds between allowed reloads
        const MAX_DISCONNECT_COUNT = 3; // Number of disconnects before we stop auto-reloading
        
        // Function to show the connection lost banner
        function showConnectionLost() {
            if (connectionBanner) {
                connectionBanner.style.display = 'block';
            }
        }
        
        // Function to hide the connection lost banner
        function hideConnectionLost() {
            if (connectionBanner) {
                connectionBanner.style.display = 'none';
            }
        }
        
        // Debounced reload function to prevent multiple rapid reloads
        function debouncedReload() {
            const now = Date.now();
            
            // Check if we should reload based on debounce time, disconnect count, and device type
            if (now - lastReconnectTime > RECONNECT_DEBOUNCE_TIME && 
                disconnectCount < MAX_DISCONNECT_COUNT && 
                !isMobileDevice) {
                
                console.log('Reloading page after reconnection');
                lastReconnectTime = now;
                disconnectCount++;
                
                // Reload with a delay to allow the connection to stabilize
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            } else {
                console.log('Skipping reload: ' + 
                    (now - lastReconnectTime <= RECONNECT_DEBOUNCE_TIME ? 'Too soon since last reload' : '') +
                    (disconnectCount >= MAX_DISCONNECT_COUNT ? 'Too many disconnects' : '') +
                    (isMobileDevice ? 'Mobile device detected' : ''));
                
                // Just hide the banner without reloading on mobile
                hideConnectionLost();
            }
        }
        
        // Monitor socket.io connection events
        const socketMonitorInterval = setInterval(function() {
            // Check if socket.io is loaded
            if (window._nicegui && window._nicegui.socket) {
                clearInterval(socketMonitorInterval);
                
                const socket = window._nicegui.socket;
                
                // Listen for disconnect events
                socket.on('disconnect', function() {
                    console.log('Socket disconnected');
                    isConnected = false;
                    showConnectionLost();
                });
                
                // Listen for reconnect events
                socket.on('connect', function() {
                    console.log('Socket connected');
                    isConnected = true;
                    
                    // Only reload if we were previously disconnected
                    if (connectionBanner && connectionBanner.style.display === 'block') {
                        debouncedReload();
                    } else {
                        hideConnectionLost();
                    }
                });
            }
        }, 100);
        
        // Add a fallback detection method using fetch API with more tolerance for mobile
        // This helps detect network issues even if socket.io doesn't report them
        let failedFetchAttempts = 0;
        const MAX_FAILED_FETCHES = isMobileDevice ? 3 : 1; // More tolerance on mobile
        
        setInterval(function() {
            if (!isConnected) {
                return; // Already know we're disconnected
            }
            
            // Try to fetch a small resource to check connection
            fetch(window.location.origin + '/health', {
                method: 'GET',
                cache: 'no-store',
                headers: {
                    'Cache-Control': 'no-cache'
                },
                // Add a timeout to the fetch request
                signal: AbortSignal.timeout(5000) // 5 second timeout
            })
            .then(response => {
                if (response.ok) {
                    // Connection is working, reset failed attempts
                    failedFetchAttempts = 0;
                    
                    if (!isConnected) {
                        console.log('Network connection restored');
                        // Don't set isConnected=true here, let socket.io handle that
                    }
                } else {
                    console.log('Network check failed with status:', response.status);
                    failedFetchAttempts++;
                    
                    if (failedFetchAttempts >= MAX_FAILED_FETCHES) {
                        showConnectionLost();
                    }
                }
            })
            .catch(error => {
                console.log('Network check failed:', error);
                failedFetchAttempts++;
                
                if (failedFetchAttempts >= MAX_FAILED_FETCHES) {
                    showConnectionLost();
                }
            });
        }, isMobileDevice ? 30000 : 15000); // Check less frequently on mobile (30s vs 15s)
    });
    </script>
    ''')

def add_css_styles() -> None:
    """Add CSS styles to the page."""
    # Add root CSS to override NiceGUI defaults
    ui.add_head_html(f'<style>{css.ROOT_CSS}</style>')
    
    # Add CSS for animations
    ui.add_head_html(f'<style>{css.habit_animations}</style>')
    
    # Add CSS for connection status indicator
    ui.add_head_html('''
        <style>
        #connection-status-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            background-color: #e53935;
            color: white;
            text-align: center;
            padding: 10px;
            font-weight: bold;
            display: none;
        }
        </style>
    ''')
    
    # Add CSS for transitions
    ui.add_head_html('''
        <style>
        .habit-card {
            transition: transform 0.3s ease-out;
            position: relative;
            overflow: hidden;
        }
        .resort-pending {
            position: relative;
        }
        .progress-bar {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 2px;
            width: 100%;
            background: #4CAF50;
            transform-origin: right;
            animation: progress-right-to-left 3s linear forwards;
        }
        
        @keyframes progress-right-to-left {
            from { transform: scaleX(1); }
            to { transform: scaleX(0); }
        }
        
        .resort-pending::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: #4CAF50;
            animation: progress 2s linear;
        }
        @keyframes progress {
            0% { width: 100%; }
            100% { width: 0%; }
        }
        .highlight-card {
            animation: highlight 1s ease-out;
        }
        @keyframes highlight {
            0% { background-color: rgba(76, 175, 80, 0.2); }
            100% { background-color: transparent; }
        }
        </style>
    ''')

def add_all_scripts() -> None:
    """Add all scripts and styles to the page."""
    add_settings_script()
    add_javascript_files()
    add_css_styles()
