document.addEventListener('DOMContentLoaded', () => {
    // Get elements from the DOM
    const registrationStatusElement = document.getElementById('registration-status');
    const openRegTile = document.getElementById('open-reg-tile');
    const closeRegTile = document.getElementById('close-reg-tile');

    // Action Confirmation Dialog Elements
    const actionConfirmationDialog = document.getElementById('action-confirmation-dialog');
    const confirmationDialogTitle = document.getElementById('confirmation-dialog-title');
    const confirmationDialogMessage = document.getElementById('confirmation-dialog-message');
    const cancelActionButton = document.getElementById('cancel-action-button');
    const confirmActionButton = document.getElementById('confirm-action-button');

    // --- NEW: Status Message Modal Elements ---
    const statusMessageModal = document.getElementById('status-message-modal');
    const statusModalTitle = document.getElementById('status-modal-title');
    const statusModalMessage = document.getElementById('status-modal-message');
    const statusModalOkButton = document.getElementById('status-modal-ok-button');

    let pendingAction = null; // To store the action ('Open Registration' or 'Close Registration')

    // ViewModel state
    const viewModel = {
        isRegistrationOpen: false, // Initial state

        setRegistrationStatus: function(isOpen) {
            this.isRegistrationOpen = isOpen;
            this.updateUI();
        },

        performAction: function(action) {
            // In a real application, you would make an API call here
            // and then show success/error based on the API response.
            if (action === 'Open Registration') {
                console.log('Opening registration...');
                this.setRegistrationStatus(true);
                showStatusModal('Success', 'Registration has been opened successfully.');
            } else if (action === 'Close Registration') {
                console.log('Closing registration...');
                this.setRegistrationStatus(false);
                showStatusModal('Success', 'Registration has been closed successfully.');
            }
            pendingAction = null; 
        },

        updateUI: function() {
            if (!registrationStatusElement || !openRegTile || !closeRegTile) {
                console.error("One or more UI elements for registration status are missing.");
                return;
            }
            if (this.isRegistrationOpen) {
                registrationStatusElement.textContent = 'Registration is Open';
                openRegTile.classList.add('disabled-tile');
                openRegTile.setAttribute('aria-disabled', 'true');
                closeRegTile.classList.remove('disabled-tile');
                closeRegTile.setAttribute('aria-disabled', 'false');
            } else {
                registrationStatusElement.textContent = 'Registration is Closed';
                closeRegTile.classList.add('disabled-tile');
                closeRegTile.setAttribute('aria-disabled', 'true');
                openRegTile.classList.remove('disabled-tile');
                openRegTile.setAttribute('aria-disabled', 'false');
            }
        }
    };

    // --- Status Message Modal Logic ---
    function showStatusModal(title, message, isSuccess = true) {
        if (!statusMessageModal || !statusModalTitle || !statusModalMessage) {
            console.error("Status message modal elements are missing.");
            alert(`${title}: ${message}`); // Fallback to alert if modal elements are not found
            return;
        }
        statusModalTitle.textContent = title;
        statusModalMessage.textContent = message;
        // Optionally, add classes for styling success/error
        statusMessageModal.classList.toggle('success-modal', isSuccess);
        statusMessageModal.classList.toggle('error-modal', !isSuccess);
        
        statusMessageModal.style.display = 'flex';
        statusMessageModal.classList.add('show');
    }

    function hideStatusModal() {
        if (statusMessageModal) {
            statusMessageModal.style.display = 'none';
            statusMessageModal.classList.remove('show');
        }
    }

    // --- Confirmation Dialog Logic ---
    function showConfirmationDialog(action) {
        if (!actionConfirmationDialog || !confirmationDialogTitle || !confirmationDialogMessage) {
            console.error("Action confirmation dialog elements are missing.");
            // Fallback: directly perform action or show an alert
            // viewModel.performAction(action); // Or alert("Confirmation dialog missing, performing action directly.")
            return;
        }
        pendingAction = action;
        if (action === 'Open Registration') {
            confirmationDialogTitle.textContent = 'Confirm Open Registration';
            confirmationDialogMessage.textContent = 'Are you sure you want to open course registration?';
        } else if (action === 'Close Registration') {
            confirmationDialogTitle.textContent = 'Confirm Close Registration';
            confirmationDialogMessage.textContent = 'Are you sure you want to close course registration?';
        }
        actionConfirmationDialog.style.display = 'flex';
        actionConfirmationDialog.classList.add('show');
    }

    function hideConfirmationDialog() {
        if (actionConfirmationDialog) {
            actionConfirmationDialog.style.display = 'none';
            actionConfirmationDialog.classList.remove('show');
        }
        // Do not clear pendingAction here if cancel is clicked, only if confirmed or overlay click.
        // Or clear it always and re-prompt if needed. For simplicity, let's clear it.
        // pendingAction = null; 
    }

    // --- Keyboard Accessibility for Tiles ---
    function handleKeydown(event, callback) {
        if (event.key === 'Enter' || event.key === ' ' || event.keyCode === 13 || event.keyCode === 32) {
            event.preventDefault();
            if (typeof callback === 'function') {
                callback();
            }
        }
    }

    // --- Event Listeners ---
    if (openRegTile) {
        const action = 'Open Registration';
        const callback = () => {
            if (!viewModel.isRegistrationOpen) {
                showConfirmationDialog(action);
            } else {
                console.log('Registration is already open.');
                showStatusModal('Information', 'Registration is already open.', true);
            }
        };
        openRegTile.addEventListener('click', callback);
        openRegTile.addEventListener('keydown', (event) => handleKeydown(event, callback));
    }

    if (closeRegTile) {
        const action = 'Close Registration';
        const callback = () => {
            if (viewModel.isRegistrationOpen) {
                showConfirmationDialog(action);
            } else {
                console.log('Registration is already closed.');
                showStatusModal('Information', 'Registration is already closed.', true);
            }
        };
        closeRegTile.addEventListener('click', callback);
        closeRegTile.addEventListener('keydown', (event) => handleKeydown(event, callback));
    }

    // Confirmation Dialog Button Listeners
    if (cancelActionButton) {
        cancelActionButton.addEventListener('click', () => {
            hideConfirmationDialog();
            pendingAction = null; // Ensure pending action is cleared on explicit cancel
        });
    }

    if (confirmActionButton) {
        confirmActionButton.addEventListener('click', () => {
            if (pendingAction) {
                viewModel.performAction(pendingAction);
            }
            hideConfirmationDialog();
            // pendingAction is cleared within performAction or hideConfirmationDialog
        });
    }
    
    if(actionConfirmationDialog){
        actionConfirmationDialog.addEventListener('click', (event) => {
            if (event.target === actionConfirmationDialog) {
                hideConfirmationDialog();
                pendingAction = null; // Ensure pending action is cleared on overlay click
            }
        });
    }

    // --- NEW: Status Message Modal OK Button Listener ---
    if (statusModalOkButton) {
        statusModalOkButton.addEventListener('click', hideStatusModal);
    }
    if (statusMessageModal) {
         statusMessageModal.addEventListener('click', (event) => {
            if (event.target === statusMessageModal) { // Clicked on the overlay
                hideStatusModal();
            }
        });
    }

    // Initial UI setup
    viewModel.updateUI();
});
