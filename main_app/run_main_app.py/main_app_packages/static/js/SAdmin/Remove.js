document.addEventListener('DOMContentLoaded', () => {
    const pageTitle = document.getElementById('page-title');
    const managersToggleBtn = document.getElementById('managers-toggle-btn');
    const staffToggleBtn = document.getElementById('staff-toggle-btn');
    const listContainer = document.getElementById('list-container');
    const emptyListMessage = document.getElementById('empty-list-message');

    const confirmationDialog = document.getElementById('confirmation-dialog');
    const dialogMessage = document.getElementById('dialog-message');
    const cancelButton = document.getElementById('cancel-button');
    const removeConfirmButton = document.getElementById('remove-confirm-button');

    let isManagerSelected = true;
    let currentItemToRemove = null; // To store which item/id to remove

    // Sample data (replace with actual data fetching if needed)
    let managers = [
        { id: 'm1', firstName: 'Alice', lastName: 'Smith', qualification: 'MBA', fieldOfQualification: 'Business' },
        { id: 'm2', firstName: 'Bob', lastName: 'Johnson', qualification: 'PhD', fieldOfQualification: 'Engineering' }
    ];
    let staff = [
        { id: 's1', firstName: 'Charlie', lastName: 'Brown', employmentType: 'Full-time' },
        { id: 's2', firstName: 'Diana', lastName: 'Prince', employmentType: 'Part-time' }
    ];

    function renderList() {
        listContainer.innerHTML = ''; // Clear previous items
        const items = isManagerSelected ? managers : staff;

        if (items.length === 0) {
            emptyListMessage.textContent = isManagerSelected ? 'No Managers Found' : 'No Staff Found';
            emptyListMessage.style.display = 'block';
            listContainer.style.display = 'none';
        } else {
            emptyListMessage.style.display = 'none';
            listContainer.style.display = 'block';
            items.forEach(item => {
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

                const deleteButton = document.createElement('button');
                deleteButton.classList.add('delete-button');
                deleteButton.innerHTML = '&#x1F5D1;'; // Trash can icon (Unicode)
                deleteButton.setAttribute('aria-label', 'Delete');
                deleteButton.onclick = () => showConfirmationDialog(item);
                listItem.appendChild(deleteButton);

                listContainer.appendChild(listItem);
            });
        }
    }

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

    function toggleSelection(selectManagers) {
        isManagerSelected = selectManagers;
        updateToggleButtons();
        renderList();
    }

    function showConfirmationDialog(item) {
        currentItemToRemove = item;
        dialogMessage.textContent = isManagerSelected
            ? `Are you sure you want to remove manager ${item.firstName} ${item.lastName}?`
            : `Are you sure you want to remove staff member ${item.firstName} ${item.lastName}?`;
        confirmationDialog.style.display = 'flex';
    }

    function hideConfirmationDialog() {
        confirmationDialog.style.display = 'none';
        currentItemToRemove = null;
    }

    function removeUser() {
        if (!currentItemToRemove) return;

        if (isManagerSelected) {
            managers = managers.filter(m => m.id !== currentItemToRemove.id);
        } else {
            staff = staff.filter(s => s.id !== currentItemToRemove.id);
        }
        hideConfirmationDialog();
        renderList();
    }

    // Event Listeners
    managersToggleBtn.addEventListener('click', () => toggleSelection(true));
    staffToggleBtn.addEventListener('click', () => toggleSelection(false));

    cancelButton.addEventListener('click', hideConfirmationDialog);
    removeConfirmButton.addEventListener('click', removeUser);

    // Close modal if clicked outside the content (optional)
    confirmationDialog.addEventListener('click', (event) => {
        if (event.target === confirmationDialog) {
            hideConfirmationDialog();
        }
    });

    // Initial Render
    updateToggleButtons();
    renderList();
});