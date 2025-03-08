from nicegui import ui, app

def add_connection_status():
    """
    Add a connection status indicator that shows when the WebSocket connection is broken.
    This adds both the UI element and the necessary JavaScript to monitor connection status.
    """
    # Create a hidden notification container that will be shown when connection is lost
    with ui.element('div').classes('fixed top-0 left-0 right-0 z-50 hidden').id('connection-status-banner'):
        with ui.element('div').classes('bg-red-600 text-white p-4 text-center font-bold'):
            ui.label('Connection lost. Waiting to reconnect...').classes('text-lg')
    
    # Add JavaScript to monitor connection status
    ui.add_head_html('''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Variables to track connection state
        let isConnected = true;
        const connectionBanner = document.getElementById('connection-status-banner');
        
        // Function to show the connection lost banner
        function showConnectionLost() {
            if (connectionBanner) {
                connectionBanner.classList.remove('hidden');
            }
        }
        
        // Function to hide the connection lost banner
        function hideConnectionLost() {
            if (connectionBanner) {
                connectionBanner.classList.add('hidden');
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
                    hideConnectionLost();
                    
                    // Reload the page to ensure all data is fresh
                    // Only reload if we were previously disconnected to avoid unnecessary reloads
                    if (connectionBanner && !connectionBanner.classList.contains('hidden')) {
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    }
                });
            }
        }, 100);
        
        // Add a fallback detection method using fetch API
        // This helps detect network issues even if socket.io doesn't report them
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
                }
            })
            .then(response => {
                if (response.ok) {
                    // Connection is working
                    if (!isConnected) {
                        console.log('Network connection restored');
                        // Don't set isConnected=true here, let socket.io handle that
                    }
                } else {
                    console.log('Network check failed with status:', response.status);
                    showConnectionLost();
                }
            })
            .catch(error => {
                console.log('Network check failed:', error);
                showConnectionLost();
            });
        }, 15000); // Check every 15 seconds
    });
    </script>
    ''')
