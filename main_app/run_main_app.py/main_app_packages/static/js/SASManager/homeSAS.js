document.addEventListener('DOMContentLoaded', () => {
    // Get elements from the DOM
    const registrationStatusElement = document.getElementById('registration-status');
    const openRegTile = document.getElementById('open-reg-tile');
    const closeRegTile = document.getElementById('close-reg-tile');

    // ViewModel state (simulating Flutter's ViewModel)
    const viewModel = {
        isRegistrationOpen: false, // Initial state

        // Method to update registration status and UI
        setRegistrationStatus: function(isOpen) {
            this.isRegistrationOpen = isOpen;
            this.updateUI();
        },

        // Method to handle tile taps
        handleTileTap: function(action) {
            if (action === 'Open Registration') {
                // Add any specific logic for opening registration here
                // For example, show a confirmation dialog or make an API call
                console.log('Attempting to open registration...');
                this.setRegistrationStatus(true);
                // You might want to show a success message or confirmation
                alert('Registration has been opened.'); // Simple alert, replace with modal if preferred
            } else if (action === 'Close Registration') {
                // Add any specific logic for closing registration here
                console.log('Attempting to close registration...');
                this.setRegistrationStatus(false);
                // You might want to show a success message or confirmation
                alert('Registration has been closed.'); // Simple alert, replace with modal if preferred
            }
        },

        // Method to update the UI based on the current state
        updateUI: function() {
            if (this.isRegistrationOpen) {
                registrationStatusElement.textContent = 'Registration is Open';
                // Optionally, disable the "Open Registration" button or change its style
                openRegTile.classList.add('disabled-tile'); // Example: add a class to style it as disabled
                closeRegTile.classList.remove('disabled-tile');
            } else {
                registrationStatusElement.textContent = 'Registration is Closed';
                // Optionally, disable the "Close Registration" button
                closeRegTile.classList.add('disabled-tile');
                openRegTile.classList.remove('disabled-tile');
            }
        }
    };

    // Event Listeners for the dashboard tiles
    if (openRegTile) {
        openRegTile.addEventListener('click', () => {
            // Prevent action if registration is already open
            if (!viewModel.isRegistrationOpen) {
                viewModel.handleTileTap('Open Registration');
            } else {
                console.log('Registration is already open.');
                // Optionally, provide feedback that it's already open
            }
        });
    }

    if (closeRegTile) {
        closeRegTile.addEventListener('click', () => {
            // Prevent action if registration is already closed
            if (viewModel.isRegistrationOpen) {
                viewModel.handleTileTap('Close Registration');
            } else {
                console.log('Registration is already closed.');
                // Optionally, provide feedback that it's already closed
            }
        });
    }

    // Initial UI setup based on the viewModel's default state
    viewModel.updateUI();
});

// Add a simple CSS class for disabled tiles (optional)
// You can add this to your style.css or here in a <style> tag in HTML
/*
.disabled-tile {
    opacity: 0.6;
    cursor: not-allowed;
    background-color: #f0f0f0; // Lighter background for disabled state
}
.disabled-tile:hover {
    transform: none;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1); // Keep original shadow
}
*/
