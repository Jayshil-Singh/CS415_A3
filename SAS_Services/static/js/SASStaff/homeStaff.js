// static/js/SASStaff/homeStaff.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("homeStaff.js: DOMContentLoaded event fired.");

    const menuButton = document.getElementById('menu-button'); 
    const drawer = document.getElementById('drawer');
    const overlay = document.getElementById('overlay');
    const welcomeMessageElement = document.getElementById('welcome-message');
    const dashboardGridElement = document.getElementById('dashboard-grid');
    const drawerItemsListElement = document.getElementById('drawer-items-list');

    let staffName = "Staff Member"; 
    let navLinks = {}; 

    const initialDataElement = document.getElementById('staff-home-initial-data');
    if (initialDataElement && initialDataElement.textContent) {
        try {
            const parsedData = JSON.parse(initialDataElement.textContent);
            staffName = parsedData.staff_name || staffName;
            navLinks = parsedData.navigation_links || {};
            console.log("JS: Staff home initial data successfully loaded and parsed:", parsedData);
        } catch (e) {
            console.error("JS: Error parsing initial data for staff home:", e, "Raw content:", initialDataElement.textContent);
        }
    } else {
        console.warn("JS: Staff home initial data script tag (#staff-home-initial-data) not found or empty.");
    }

    if (welcomeMessageElement) {
        welcomeMessageElement.textContent = `Welcome, ${staffName}!`;
    } else {
        console.error("JS ERROR: Welcome message element (#welcome-message) not found.");
    }

    const staffDashboardItems = [
        { icon: 'person_add', title: 'Register Student', actionKey: 'navigateToRegister' },
        { icon: 'edit', title: 'Edit Student', actionKey: 'navigateToEdit' },
        { icon: 'grading', title: 'Manage Student Grades', actionKey: 'navigateToAllSTGrades' }, // ADDED TILE for allST.html
        { icon: 'fact_check', title: 'Grade Rechecks', actionKey: 'navigateToGradeRecheck' }, 
        { icon: 'pause_circle_filled', title: 'Put on Hold', actionKey: 'putStudentOnHold' } 
    ];

    const drawerMenuItems = [
        { icon: 'dashboard', title: 'Staff Dashboard', actionKey: 'navigateToStaffHome' },
        { icon: 'person_add', title: 'Register Student', actionKey: 'navigateToRegister' },
        { icon: 'edit', title: 'Edit Student', actionKey: 'navigateToEdit' },
        { icon: 'grading', title: 'Manage Student Grades', actionKey: 'navigateToAllSTGrades' }, // ADDED TO DRAWER
        { icon: 'fact_check', title: 'Grade Rechecks', actionKey: 'navigateToGradeRecheck' }, 
        { icon: 'pause_circle_filled', title: 'Put Student on Hold', actionKey: 'putStudentOnHold' }
    ];
    
    if (!navLinks.navigateToStaffHome) { 
        navLinks.navigateToStaffHome = navLinks.navigateToStaffHome || window.location.pathname; 
        console.warn("JS: 'navigateToStaffHome' not found in navLinks, defaulting to current path:", navLinks.navigateToStaffHome);
    }

    function openDrawer() {
        if (drawer) drawer.classList.add('open');
        if (overlay) {
            overlay.style.display = 'block'; 
            setTimeout(() => overlay.classList.add('active'), 10); 
        }
        if (menuButton) menuButton.setAttribute('aria-expanded', 'true');
        console.log("JS: Drawer opened.");
    }

    function closeDrawer() {
        if (drawer) drawer.classList.remove('open');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => { 
                if (!overlay.classList.contains('active')) overlay.style.display = 'none';
            }, 300); 
        }
        if (menuButton) menuButton.setAttribute('aria-expanded', 'false');
        console.log("JS: Drawer closed.");
    }

    if (menuButton) {
        menuButton.addEventListener('click', (event) => {
            event.stopPropagation();
            if (drawer && drawer.classList.contains('open')) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    } else {
        console.warn("JS WARNING: Staff drawer menu button (#menu-button) not found in shared header.");
    }

    if (overlay) {
        overlay.addEventListener('click', closeDrawer);
    } else {
        console.warn("JS WARNING: Overlay element (#overlay) not found.");
    }
    document.addEventListener('keydown', (event) => { 
        if (event.key === 'Escape' && drawer && drawer.classList.contains('open')) {
            closeDrawer();
        }
    });

    if (drawerItemsListElement) {
        console.log("JS: Rendering drawer items...");
        drawerItemsListElement.innerHTML = ''; 
        drawerMenuItems.forEach(item => {
            const link = document.createElement('a');
            link.href = navLinks[item.actionKey] || '#'; 
            link.classList.add('drawer-item-link');
            link.setAttribute('role', 'menuitem');

            const listItemContent = document.createElement('div'); 
            listItemContent.classList.add('drawer-item');
            
            listItemContent.innerHTML = `
                <span class="material-icons drawer-item-icon">${item.icon}</span>
                <span class="drawer-item-text">${item.title}</span>
            `;
            
            if (item.actionKey === 'putStudentOnHold' && !navLinks[item.actionKey]) {
                link.href = "javascript:void(0);"; 
                listItemContent.addEventListener('click', (e) => {
                    e.preventDefault();
                    alert("JS Action: Put Student on Hold (from Drawer)"); 
                    closeDrawer();
                });
            }
            link.appendChild(listItemContent);
            drawerItemsListElement.appendChild(link); 
        });
        console.log("JS: Drawer items rendered.");
    } else {
        console.error("JS ERROR: Drawer items list element (#drawer-items-list) not found.");
    }

    if (dashboardGridElement) {
        console.log("JS: Rendering dashboard cards...");
        dashboardGridElement.innerHTML = ''; 
        staffDashboardItems.forEach(item => {
            const link = document.createElement('a');
            link.href = navLinks[item.actionKey] || '#'; 
            link.classList.add('dashboard-card-link');
            link.setAttribute('aria-label', item.title);

            const card = document.createElement('div');
            card.classList.add('dashboard-card');
            
            card.innerHTML = `
                <span class="material-icons card-icon">${item.icon}</span>
                <p class="card-title">${item.title}</p>
            `;
            
            if (item.actionKey === 'putStudentOnHold' && !navLinks[item.actionKey]) {
                link.href = "javascript:void(0);";
                card.style.cursor = 'pointer';
                card.setAttribute('role', 'button');
                card.setAttribute('tabindex', '0'); 

                const cardAction = () => {
                    alert("JS Action: Put Student on Hold (from Card)");
                };

                card.addEventListener('click', (e) => { 
                    e.preventDefault(); 
                    cardAction(); 
                });
                card.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') { 
                        event.preventDefault(); 
                        cardAction(); 
                    }
                });
            }
            link.appendChild(card);
            dashboardGridElement.appendChild(link);
        });
        console.log("JS: Dashboard cards rendered.");
    } else {
        console.error("JS ERROR: Dashboard grid element (#dashboard-grid) not found.");
    }
    
    console.log("JS: Staff home page script fully initialized.");
});