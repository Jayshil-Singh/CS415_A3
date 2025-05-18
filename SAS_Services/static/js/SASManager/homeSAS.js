// static/js/SASManager/homeSAS.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("homeSAS.js: DOMContentLoaded");

    // Get elements from the DOM
    const registrationStatusElement = document.getElementById('registration-status');
    const statusContainer = registrationStatusElement ? registrationStatusElement.closest('.status-container') : null;
    const openRegTile = document.getElementById('open-reg-tile');
    const closeRegTile = document.getElementById('close-reg-tile');

    // Action Confirmation Dialog Elements
    const actionConfirmationDialog = document.getElementById('action-confirmation-dialog');
    const confirmationDialogTitle = document.getElementById('confirmation-dialog-title');
    const confirmationDialogMessage = document.getElementById('confirmation-dialog-message');
    const cancelActionButton = document.getElementById('cancel-action-button');
    const confirmActionButton = document.getElementById('confirm-action-button');

    // Status Message Modal Elements
    const statusMessageModal = document.getElementById('status-message-modal');
    const statusModalTitle = document.getElementById('status-modal-title');
    const statusModalMessage = document.getElementById('status-modal-message');
    const statusModalOkButton = document.getElementById('status-modal-ok-button');

    let pendingAction = null;

    const viewModel = {
        isRegistrationOpen: false, // Initial state, fetched by fetchInitialStatus

        async fetchInitialStatus() {
            console.log("JS: Fetching initial registration status (mock)...");
            return new Promise(resolve => {
                setTimeout(() => {
                    // In a real app, this would be the actual status from the server.
                    // For testing, let's assume it's initially closed.
                    console.log("JS: Mock initial status is 'Closed'");
                    resolve(false); 
                }, 200);
            });
        },

        async submitRegistrationChange(targetStateIsOpen) {
            const action = targetStateIsOpen ? 'Open' : 'Close';
            console.log(`JS: Submitting registration change to ${action} (mock)...`);
            // Simulate API call - MODIFIED TO ALWAYS SUCCEED FOR DEBUGGING
            return new Promise(resolve => {
                setTimeout(() => {
                    console.log(`JS: Mock API call to ${action} registration successful.`);
                    resolve({ success: true, message: `Registration has been ${action.toLowerCase()}ed successfully.` });
                }, 800);
            });
        },

        setRegistrationStatus: function(isOpen) {
            console.log(`JS: Setting internal registration status to: ${isOpen ? 'Open' : 'Closed'}`);
            this.isRegistrationOpen = isOpen;
            this.updateUI();
        },

        performAction: async function(actionToPerform) {
            console.log(`JS: Performing action: ${actionToPerform}`);
            const targetStateIsOpen = actionToPerform === 'Open Registration';
            
            const response = await this.submitRegistrationChange(targetStateIsOpen);

            if (response.success) {
                this.setRegistrationStatus(targetStateIsOpen); // This will call updateUI
                showStatusModal('Success', response.message, true);
            } else {
                // This case should not be hit with the current always-succeeding mock
                showStatusModal('Error', response.message, false);
            }
            pendingAction = null; 
        },

        updateUI: function() {
            console.log("JS: Updating UI based on status. isRegistrationOpen:", this.isRegistrationOpen);
            if (!registrationStatusElement || !openRegTile || !closeRegTile || !statusContainer) {
                console.error("JS Error: One or more UI elements for registration status are missing.");
                return;
            }

            statusContainer.classList.remove('open-status', 'closed-status');

            if (this.isRegistrationOpen) {
                registrationStatusElement.textContent = 'Registration is Open';
                statusContainer.classList.add('open-status');

                openRegTile.classList.add('disabled'); // Use 'disabled' for CSS
                openRegTile.setAttribute('aria-disabled', 'true');
                openRegTile.setAttribute('tabindex', '-1');

                closeRegTile.classList.remove('disabled');
                closeRegTile.setAttribute('aria-disabled', 'false');
                closeRegTile.setAttribute('tabindex', '0');
            } else {
                registrationStatusElement.textContent = 'Registration is Closed';
                statusContainer.classList.add('closed-status');

                closeRegTile.classList.add('disabled');
                closeRegTile.setAttribute('aria-disabled', 'true');
                closeRegTile.setAttribute('tabindex', '-1');

                openRegTile.classList.remove('disabled');
                openRegTile.setAttribute('aria-disabled', 'false');
                openRegTile.setAttribute('tabindex', '0');
            }
            console.log("JS: UI Update complete.");
        }
    };

    function showModal(modalElement) {
        if (!modalElement) {
            console.error("JS Error: Attempted to show a non-existent modal.");
            return;
        }
        console.log(`JS: Showing modal: ${modalElement.id}`);
        modalElement.style.display = 'flex';
        setTimeout(() => { 
            modalElement.classList.add('active'); // Use 'active' for CSS transitions
        }, 10);
    }

    function hideModal(modalElement) {
        if (!modalElement) {
            console.error("JS Error: Attempted to hide a non-existent modal.");
            return;
        }
        console.log(`JS: Hiding modal: ${modalElement.id}`);
        modalElement.classList.remove('active');
        setTimeout(() => { 
            if (!modalElement.classList.contains('active')) {
                 modalElement.style.display = 'none';
            }
        }, 300); // Match CSS transition duration
    }

    function showStatusModal(title, message, isSuccess = true) {
        if (!statusMessageModal || !statusModalTitle || !statusModalMessage || !statusModalOkButton) {
            console.error("JS Error: Status message modal elements are missing.");
            alert(`${title}: ${message}`); 
            return;
        }
        statusModalTitle.textContent = title;
        statusModalMessage.textContent = message;
        
        statusMessageModal.classList.remove('success-modal', 'error-modal');
        statusMessageModal.classList.add(isSuccess ? 'success-modal' : 'error-modal');
        
        showModal(statusMessageModal);
    }

    function hideStatusModal() {
        hideModal(statusMessageModal);
    }

    function showConfirmationDialog(action) {
        if (!actionConfirmationDialog || !confirmationDialogTitle || !confirmationDialogMessage || !confirmActionButton || !cancelActionButton) {
            console.error("JS Error: Action confirmation dialog elements are missing.");
            return;
        }
        pendingAction = action;
        confirmationDialogTitle.textContent = `Confirm ${action}`;
        confirmationDialogMessage.textContent = `Are you sure you want to ${action.toLowerCase()}?`;
        showModal(actionConfirmationDialog);
    }

    function hideConfirmationDialog() {
        hideModal(actionConfirmationDialog);
    }

    function handleKeydown(event, callback) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            if (typeof callback === 'function') {
                callback();
            }
        }
    }

    function setupEventListeners() {
        console.log("JS: Setting up event listeners.");
        if (openRegTile) {
            const action = 'Open Registration';
            const callback = () => {
                console.log("JS: Open Registration tile clicked/activated.");
                if (openRegTile.classList.contains('disabled')) {
                    console.log("JS: Open Registration tile is disabled, action ignored.");
                    return; 
                }
                // This logic was in your previous JS: if (!viewModel.isRegistrationOpen)
                // It's correct because you only open if it's currently closed.
                if (!viewModel.isRegistrationOpen) {
                    showConfirmationDialog(action);
                } else {
                    showStatusModal('Information', 'Registration is already open.', true);
                }
            };
            openRegTile.addEventListener('click', callback);
            openRegTile.addEventListener('keydown', (event) => handleKeydown(event, callback));
        } else {
            console.warn("JS Warning: openRegTile not found.");
        }

        if (closeRegTile) {
            const action = 'Close Registration';
            const callback = () => {
                console.log("JS: Close Registration tile clicked/activated.");
                if (closeRegTile.classList.contains('disabled')) {
                    console.log("JS: Close Registration tile is disabled, action ignored.");
                    return;
                }
                // This logic was in your previous JS: if (viewModel.isRegistrationOpen)
                // It's correct because you only close if it's currently open.
                if (viewModel.isRegistrationOpen) {
                    showConfirmationDialog(action);
                } else {
                    showStatusModal('Information', 'Registration is already closed.', true);
                }
            };
            closeRegTile.addEventListener('click', callback);
            closeRegTile.addEventListener('keydown', (event) => handleKeydown(event, callback));
        } else {
            console.warn("JS Warning: closeRegTile not found.");
        }

        if (cancelActionButton) {
            cancelActionButton.addEventListener('click', () => {
                console.log("JS: Cancel button clicked in confirmation dialog.");
                hideConfirmationDialog();
                pendingAction = null; 
            });
        } else {
            console.warn("JS Warning: cancelActionButton not found.");
        }

        // Re-cloning the confirm button to ensure fresh event listener
        // This is a robust way to handle dynamic event assignment for the confirm button
        if (confirmActionButton && actionConfirmationDialog) {
            const newConfirmButton = confirmActionButton.cloneNode(true);
            confirmActionButton.parentNode.replaceChild(newConfirmButton, confirmActionButton);
            // confirmActionButton = newConfirmButton; // Update reference if needed elsewhere

            newConfirmButton.addEventListener('click', () => {
                console.log("JS: Confirm button clicked. Pending action:", pendingAction);
                if (pendingAction) {
                    viewModel.performAction(pendingAction);
                }
                hideConfirmationDialog();
            });
        } else {
            console.warn("JS Warning: confirmActionButton or its parent not found for re-binding.");
        }
        
        if(actionConfirmationDialog){
            actionConfirmationDialog.addEventListener('click', (event) => {
                if (event.target === actionConfirmationDialog) { // Clicked on overlay
                    console.log("JS: Clicked on confirmation dialog overlay.");
                    hideConfirmationDialog();
                    pendingAction = null; 
                }
            });
        }

        if (statusModalOkButton) {
            statusModalOkButton.addEventListener('click', hideStatusModal);
        } else {
            console.warn("JS Warning: statusModalOkButton not found.");
        }

        if (statusMessageModal) {
            statusMessageModal.addEventListener('click', (event) => {
                if (event.target === statusMessageModal) { 
                    console.log("JS: Clicked on status message modal overlay.");
                    hideStatusModal();
                }
            });
        }
    }
    
    async function initializePage() {
        console.log("JS: Initializing page...");
        if (!registrationStatusElement) { // Early exit if critical element is missing
            console.error("JS FATAL: registrationStatusElement not found. Cannot initialize page status.");
            return;
        }
        registrationStatusElement.textContent = 'Fetching status...'; // Initial placeholder
        const initialStatusIsOpen = await viewModel.fetchInitialStatus();
        viewModel.setRegistrationStatus(initialStatusIsOpen);
        // updateUI is called by setRegistrationStatus
        console.log("JS: Page initialized.");
    }

    // Check if all essential elements are present before initializing
    if (registrationStatusElement && openRegTile && closeRegTile && 
        actionConfirmationDialog && statusMessageModal) {
        initializePage();
        setupEventListeners();
    } else {
        console.error("JS FATAL: Not all essential page elements were found. Aborting full initialization.");
        // You could display a more user-friendly error message on the page itself here
        if (registrationStatusElement) {
            registrationStatusElement.textContent = "Error: Page components missing.";
            registrationStatusElement.style.color = "red";
        }
    }
});