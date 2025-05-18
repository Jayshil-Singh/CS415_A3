document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - CRITICAL: These must be defined
    const menuButton = document.getElementById('menu-button');
    const drawer = document.getElementById('drawer');
    const overlay = document.getElementById('overlay');
    const welcomeMessageElement = document.getElementById('welcome-message');
    const dashboardGridElement = document.getElementById('dashboard-grid');
    const drawerItemsListElement = document.getElementById('drawer-items-list');

    let staffName = "Staff Member"; // Default
    let navLinks = {}; // This will be populated with URLs from Flask

    const initialDataElement = document.getElementById('staff-home-initial-data');
    if (initialDataElement) {
        try {
            const parsedData = JSON.parse(initialDataElement.textContent);
            staffName = parsedData.staff_name || staffName;
            navLinks = parsedData.navigation_links || {}; // navLinks gets populated here
            console.log("JS: Staff home initial data loaded:", parsedData);
        } catch (e) {
            console.error("JS: Error parsing initial data for staff home:", e);
        }
    } else {
        console.warn("JS: Staff home initial data script tag not found.");
    }

    // Update welcome message
    if (welcomeMessageElement) {
        welcomeMessageElement.textContent = `Welcome, ${staffName}!`;
    }

    // --- Data for Dashboard and Drawer ---
    // Ensure actionKey matches keys in navigation_links from app.py
    const staffDashboardItems = [
        { icon: 'person_add', title: 'Register Student', actionKey: 'navigateToRegister' },
        { icon: 'edit', title: 'Edit Student', actionKey: 'navigateToEdit' },
        { icon: 'pause_circle_filled', title: 'Put on Hold', actionKey: 'putStudentOnHold' }
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
    }

    function closeDrawer() {
        if (drawer) drawer.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }

    if (menuButton) {
        menuButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent click from bubbling up to document
            if (drawer && drawer.classList.contains('open')) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    } else {
        console.warn("JS: Menu button (#menu-button) not found.");
    }

    if (overlay) {
        overlay.addEventListener('click', closeDrawer);
    }

    // Render Drawer Items as Links
    if (drawerItemsListElement) {
        drawerItemsListElement.innerHTML = ''; // Clear any existing
        drawerMenuItems.forEach(item => {
            const link = document.createElement('a');
            link.href = navLinks[item.actionKey] || '#'; // Fallback to '#' if no URL found
            link.classList.add('drawer-item-link');

            const listItem = document.createElement('li');
            listItem.classList.add('drawer-item');
            listItem.setAttribute('role', 'menuitem');
            listItem.setAttribute('tabindex', '0'); // Make focusable
            listItem.innerHTML = `
                <span class="material-icons drawer-item-icon">${item.icon}</span>
                <span class="drawer-item-text">${item.title}</span>
            `;

            // Handle JS-specific actions or navigation
            if (item.actionKey === 'putStudentOnHold' && !navLinks[item.actionKey]) {
                // This item is a JS action, not a navigation link
                listItem.addEventListener('click', () => {
                    console.log("JS: Action - Put Student on Hold (Drawer - JS simulated)");
                    alert("JS Action: Put Student on Hold");
                    closeDrawer(); // Close drawer after action
                });
                listItem.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault(); // Prevent default space scroll
                        console.log("JS: Action - Put Student on Hold (Drawer - JS simulated via keydown)");
                        alert("JS Action: Put Student on Hold");
                        closeDrawer();
                    }
                });
            } else {
                // This item is a navigation link (handled by <a> tag)
                // Add keydown for accessibility to activate the link within
                listItem.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        link.click(); // Simulate click on the parent link
                    }
                });
            }
            link.appendChild(listItem);
            drawerItemsListElement.appendChild(link);
        });
    } else {
        console.error("JS: Drawer items list element (#drawer-items-list) not found.");
    }

    // Render Dashboard Cards as Links
    if (dashboardGridElement) {
        dashboardGridElement.innerHTML = ''; // Clear any existing
        staffDashboardItems.forEach(item => {
            const link = document.createElement('a');
            link.href = navLinks[item.actionKey] || '#'; // Fallback to '#'
            link.classList.add('dashboard-card-link');

            const card = document.createElement('div');
            card.classList.add('dashboard-card');
            // card.setAttribute('role', 'link'); // The <a> tag is the link.
            // card.setAttribute('tabindex', '0'); // The <a> tag is focusable.
            card.innerHTML = `
                <span class="material-icons card-icon">${item.icon}</span>
                <p class="card-title">${item.title}</p>
            `;

            // Handle JS-specific actions or navigation
            if (item.actionKey === 'putStudentOnHold' && !navLinks[item.actionKey]) {
                // This card is a JS action
                card.style.cursor = 'pointer'; // Indicate it's clickable
                card.setAttribute('role', 'button');
                card.setAttribute('tabindex', '0'); // Make card focusable if it's a JS action
                card.addEventListener('click', () => {
                    console.log("JS: Action - Put Student on Hold (Dashboard - JS simulated)");
                    alert("JS Action: Put Student on Hold");
                });
                card.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        console.log("JS: Action - Put Student on Hold (Dashboard - JS simulated via keydown)");
                        alert("JS Action: Put Student on Hold");
                    }
                });
            }
            // For items that are pure links, the parent <a> tag handles the click and focus.

            link.appendChild(card);
            dashboardGridElement.appendChild(link);
        });
    } else {
        console.error("JS: Dashboard grid element (#dashboard-grid) not found.");
    }

    console.log("JS: Staff home page fully initialized.");
});