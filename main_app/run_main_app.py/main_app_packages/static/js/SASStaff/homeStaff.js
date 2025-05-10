document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const menuButton = document.getElementById('menu-button');
    const drawer = document.getElementById('drawer');
    const overlay = document.getElementById('overlay');
    const mainContent = document.getElementById('main-content'); // To push content
    const welcomeMessageElement = document.getElementById('welcome-message');
    const dashboardGridElement = document.getElementById('dashboard-grid');
    const drawerItemsListElement = document.getElementById('drawer-items-list');

    // --- ViewModel Simulation ---
    const viewModel = {
        staffName: "Jane Doe", // Example staff name
        // Navigation functions (will just log to console for this example)
        navigateToRegister: function() {
            console.log("Navigating to Register Student page...");
            alert("Action: Navigate to Register Student");
            closeDrawer();
        },
        navigateToEdit: function() {
            console.log("Navigating to Edit Student page...");
            alert("Action: Navigate to Edit Student");
            closeDrawer();
        },
        putStudentOnHold: function() {
            console.log("Action: Put Student on Hold...");
            alert("Action: Put Student on Hold");
            closeDrawer();
        }
        // Add other navigation/action functions from your ViewModel as needed
    };

    // --- Data for Dashboard and Drawer ---
    // (Corresponds to Flutter's `staffItems` and drawer items)
    const staffDashboardItems = [
        { icon: 'person_add', title: 'Register Student', actionKey: 'navigateToRegister' },
        { icon: 'edit', title: 'Edit Student', actionKey: 'navigateToEdit' },
        { icon: 'pause_circle_filled', title: 'Put on Hold', actionKey: 'putStudentOnHold' }
        // Add more items as needed
    ];

    const drawerMenuItems = [
        { icon: 'person_add', title: 'Register Student', actionKey: 'navigateToRegister' },
        { icon: 'edit', title: 'Edit Student', actionKey: 'navigateToEdit' },
        { icon: 'pause_circle_filled', title: 'Put Student on Hold', actionKey: 'putStudentOnHold' }
    ];

    // --- Drawer Logic ---
    function openDrawer() {
        if (drawer) drawer.classList.add('open');
        if (overlay) overlay.classList.add('active');
        // Optional: push main content to the right
        // if (mainContent) mainContent.style.marginLeft = '280px';
        // if (document.getElementById('custom-header')) document.getElementById('custom-header').style.marginLeft = '280px';
    }

    function closeDrawer() {
        if (drawer) drawer.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        // Optional: reset main content margin
        // if (mainContent) mainContent.style.marginLeft = '0';
        // if (document.getElementById('custom-header')) document.getElementById('custom-header').style.marginLeft = '0';
    }

    if (menuButton) {
        menuButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent click from bubbling to overlay if menu button is part of header
            if (drawer.classList.contains('open')) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeDrawer);
    }


    // --- Dynamic Content Rendering ---

    // Update Welcome Message
    if (welcomeMessageElement) {
        welcomeMessageElement.textContent = `Welcome, ${viewModel.staffName}!`;
    }

    // Render Drawer Items
    if (drawerItemsListElement) {
        drawerMenuItems.forEach(item => {
            const listItem = document.createElement('li');
            listItem.classList.add('drawer-item');
            listItem.innerHTML = `
                <span class="material-icons">${item.icon}</span>
                <span>${item.title}</span>
            `;
            listItem.addEventListener('click', () => {
                if (viewModel[item.actionKey] && typeof viewModel[item.actionKey] === 'function') {
                    viewModel[item.actionKey](); // Calls the corresponding function in viewModel
                } else {
                    console.warn(`Action ${item.actionKey} not found in viewModel.`);
                }
            });
            drawerItemsListElement.appendChild(listItem);
        });
    }

    // Render Dashboard Cards
    if (dashboardGridElement) {
        staffDashboardItems.forEach(item => {
            const card = document.createElement('div');
            card.classList.add('dashboard-card');

            const iconElement = document.createElement('span');
            iconElement.classList.add('material-icons');
            iconElement.textContent = item.icon;

            const titleElement = document.createElement('p');
            titleElement.classList.add('dashboard-card-title');
            titleElement.textContent = item.title;

            card.appendChild(iconElement);
            card.appendChild(titleElement);

            card.addEventListener('click', () => {
                if (viewModel[item.actionKey] && typeof viewModel[item.actionKey] === 'function') {
                    viewModel[item.actionKey](); // Calls the corresponding function in viewModel
                } else {
                    console.warn(`Action ${item.actionKey} not found or not a function in viewModel.`);
                    alert(`Action: ${item.title}`); // Fallback alert
                }
            });
            dashboardGridElement.appendChild(card);
        });
    }

    // --- Initial Setup ---
    // (No specific initial setup needed beyond rendering for this example)

});
