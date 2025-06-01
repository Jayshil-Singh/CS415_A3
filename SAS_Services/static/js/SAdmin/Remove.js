// Wait for the HTML content to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', () => {
    // Get references to various HTML elements
    const pageTitle = document.getElementById('page-title');
    const managersToggleBtn = document.getElementById('managers-toggle-btn');
    const staffToggleBtn = document.getElementById('staff-toggle-btn');
    const listContainer = document.getElementById('list-container');
    const emptyListMessage = document.getElementById('empty-list-message');

    // Get references to the confirmation dialog elements
    const confirmationDialog = document.getElementById('confirmation-dialog');
    const dialogMessage = document.getElementById('dialog-message');
    const cancelButton = document.getElementById('cancel-button'); // The "Cancel" button in the dialog
    const removeConfirmButton = document.getElementById('remove-confirm-button'); // The "Remove" (confirm) button in the dialog

    // State variables
    let isManagerSelected = true; // To track if "Managers" or "Staff" view is active
    let currentItemToRemove = null; // To store the item (manager or staff) that the user intends to remove

    // Sample data (in a real application, this would likely be fetched from a server)
    let managers = [
        { id: 'm1', firstName: 'Alice', lastName: 'Smith', qualification: 'MBA', fieldOfQualification: 'Business' },
        { id: 'm2', firstName: 'Bob', lastName: 'Johnson', qualification: 'PhD', fieldOfQualification: 'Engineering' }
    ];
    let staff = [
        { id: 's1', firstName: 'Charlie', lastName: 'Brown', employmentType: 'Full-time' },
        { id: 's2', firstName: 'Diana', lastName: 'Prince', employmentType: 'Part-time' }
    ];

    /**
     * Renders the list of managers or staff members in the UI.
     */
    function renderList() {
        listContainer.innerHTML = ''; // Clear any existing items from the list
        const items = isManagerSelected ? managers : staff; // Determine which list to display

        if (items.length === 0) {
            // If the list is empty, show a message
            emptyListMessage.textContent = isManagerSelected ? 'No Managers Found' : 'No Staff Found';
            emptyListMessage.style.display = 'block'; // Make the empty message visible
            listContainer.style.display = 'none'; // Hide the list container
        } else {
            // If there are items, hide the empty message and show the list
            emptyListMessage.style.display = 'none';
            listContainer.style.display = 'block';
            items.forEach(item => {
                // Create HTML elements for each item in the list
                const listItem = document.createElement('div');
                listItem.classList.add('list-item');

                const itemDetails = document.createElement('div');
                itemDetails.classList.add('item-details');

                const name = document.createElement('h3');
                name.textContent = `${item.firstName} ${item.lastName}`;
                itemDetails.appendChild(name);

                const subtitle = document.createElement('p');
                if (isManagerSelected) {
                    subtitle.textContent = `Qualification: ${item.qualification}\nField: ${item.fieldOfQualification}`;
                } else {
                    subtitle.textContent = `Employment Type: ${item.employmentType}`;
                }
                itemDetails.appendChild(subtitle);
                listItem.appendChild(itemDetails);

                // Create a delete button for each item
                const deleteButton = document.createElement('button');
                deleteButton.classList.add('delete-button');
                deleteButton.innerHTML = '&#x1F5D1;'; // Unicode for trash can icon
                deleteButton.setAttribute('aria-label', 'Delete');
                // When the delete button is clicked, show the confirmation dialog
                deleteButton.onclick = () => showConfirmationDialog(item);
                listItem.appendChild(deleteButton);

                listContainer.appendChild(listItem);
            });
        }
    }

    /**
     * Updates the appearance and text of the toggle buttons and page title.
     */
    function updateToggleButtons() {
        if (isManagerSelected) {
            managersToggleBtn.classList.add('selected');
            staffToggleBtn.classList.remove('selected');
            pageTitle.textContent = 'View & Remove Managers';
        } else {
            staffToggleBtn.classList.add('selected');
            managersToggleBtn.classList.remove('selected');
            pageTitle.textContent = 'View & Remove Staff';
        }
    }

    /**
     * Toggles the selection between managers and staff.
     * @param {boolean} selectManagers - True to select managers, false to select staff.
     */
    function toggleSelection(selectManagers) {
        isManagerSelected = selectManagers;
        updateToggleButtons(); // Update button styles and title
        renderList(); // Re-render the list with the new selection
    }

    // --- Confirmation Dialog Logic ---
    /**
     * Displays the confirmation dialog.
     * @param {object} item - The manager or staff object to be potentially removed.
     */
    function showConfirmationDialog(item) {
        currentItemToRemove = item; // Store the item that might be removed
        // Set the dialog message based on whether a manager or staff is being removed
        dialogMessage.textContent = isManagerSelected
            ? `Are you sure you want to remove manager ${item.firstName} ${item.lastName}?`
            : `Are you sure you want to remove staff member ${item.firstName} ${item.lastName}?`;
        confirmationDialog.style.display = 'flex'; // Make the dialog visible
    }

    /**
     * Hides the confirmation dialog.
     */
    function hideConfirmationDialog() {
        confirmationDialog.style.display = 'none'; // Hide the dialog
        currentItemToRemove = null; // Clear the item to remove
    }

    /**
     * Removes the user (manager or staff) from the local data array and re-renders the list.
     * This function is called when the "Remove" button in the confirmation dialog is clicked.
     */
    function removeUser() {
        if (!currentItemToRemove) return; // Do nothing if no item is selected for removal

        // Filter out the item to be removed from the appropriate array
        if (isManagerSelected) {
            managers = managers.filter(m => m.id !== currentItemToRemove.id);
        } else {
            staff = staff.filter(s => s.id !== currentItemToRemove.id);
        }
        hideConfirmationDialog(); // Close the dialog
        renderList(); // Refresh the list in the UI
        // In a real application, you would also send a request to a server here to delete the user from the database.
    }

    // --- Event Listeners ---
    // Add click listeners to the toggle buttons
    managersToggleBtn.addEventListener('click', () => toggleSelection(true));
    staffToggleBtn.addEventListener('click', () => toggleSelection(false));

    // Add click listeners for the confirmation dialog buttons
    cancelButton.addEventListener('click', hideConfirmationDialog); // Handles the "Cancel" action
    removeConfirmButton.addEventListener('click', removeUser);      // Handles the "Remove" (confirm) action

    // Optional: Close the dialog if the user clicks outside the modal content
    confirmationDialog.addEventListener('click', (event) => {
        if (event.target === confirmationDialog) { // Check if the click was on the modal backdrop
            hideConfirmationDialog();
        }
    });

    // --- Initial Page Setup ---
    // Set the initial state of toggle buttons and render the initial list
    updateToggleButtons();
    renderList();
});
