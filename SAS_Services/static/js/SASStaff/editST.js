// static/js/SASStaff/editST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("editST.js: DOMContentLoaded - Initializing for Student Records Overview Page");

    // DOM Elements for the overview page
    const loadingIndicator = document.getElementById('loading-indicator');
    const noStudentsMessage = document.getElementById('no-students-message');
    const studentTableContainer = document.getElementById('student-table-container');
    // Assuming the table body ID in your simplified editST.html is 'students-table-body'
    const studentsTableBody = document.getElementById('students-table-body');
    const snackbar = document.getElementById('snackbar'); // Kept in case of any general notifications

    // Check critical elements for the overview page
    if (!loadingIndicator || !noStudentsMessage || !studentTableContainer || !studentsTableBody) {
        console.error("JS FATAL: Core page structure elements for student overview are missing!");
        if(loadingIndicator) {
            loadingIndicator.style.display = 'block'; // Ensure it's visible to show the error
            loadingIndicator.innerHTML = "<p style='color:red;'>Error: Page structure incomplete. Cannot display records.</p>";
        }
        return; // Stop further execution
    }
    console.log("JS: Core page structure elements for overview found.");

    function showLoading(isLoading) {
        if (loadingIndicator) {
            // Use 'flex' if your loading indicator CSS uses flexbox for centering, otherwise 'block'
            loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        }
    }

    function showSnackbar(message, isSuccess = true) {
        if (!snackbar) {
            console.warn("JS WARN: Snackbar element not found. Message:", message);
            // Fallback to alert if snackbar is crucial and missing, though for overview page it might be less used.
            // alert(message); 
            return;
        }
        snackbar.textContent = message;
        snackbar.className = 'snackbar'; // Reset classes
        if (isSuccess) {
            snackbar.classList.add('success');
        } else {
            snackbar.classList.add('error');
        }
        snackbar.classList.add('show');
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000);
    }

    function updateStudentListView() {
        // This function assumes student data list is rendered by the server (Jinja2) into the table.
        // It primarily manages the visibility of the table versus the "no students" message.
        console.log("JS: updateStudentListView called.");
        
        // Hide loader as server has rendered the content or lack thereof
        showLoading(false);

        // Check if the Jinja template rendered any student rows into the studentsTableBody.
        // A simple check: does the tbody have any TR children?
        // And also ensure it's not just a "no data found" row if your Jinja template renders one.
        const hasStudents = studentsTableBody && studentsTableBody.children.length > 0 &&
                            !studentsTableBody.querySelector('td[colspan="3"]'); // Adjust colspan if your "no data" row has a different one

        if (hasStudents) {
            if (studentTableContainer) studentTableContainer.style.display = 'block';
            if (noStudentsMessage) noStudentsMessage.style.display = 'none';
            console.log("JS: Student records found and displayed (likely server-rendered).");
        } else {
            if (studentTableContainer) studentTableContainer.style.display = 'none';
            if (noStudentsMessage) noStudentsMessage.style.display = 'block';
            console.log("JS: No student records found, or 'no data' message shown by server.");
        }

        // OPTIONAL: If you want to make entire table rows clickable (instead of just the link in the ID cell)
        // Make sure your <tr> elements in editST.html have class="student-link-row" and data-href="{{ url_for(...) }}"
        /*
        document.querySelectorAll('tr.student-link-row').forEach(row => {
            row.addEventListener('click', () => {
                const href = row.dataset.href;
                if (href) {
                    window.location.href = href;
                } else {
                    console.warn("JS: Clickable row is missing data-href attribute.");
                }
            });
        });
        */
    }

    // --- Initial Load ---
    // Call on load to set initial visibility based on what the server rendered.
    // The loading indicator is primarily for scenarios where JS fetches data,
    // but can be briefly shown then hidden if desired for perceived performance.
    showLoading(true); // Briefly show loader
    
    // Use a small timeout to ensure the browser has rendered the initial HTML from Jinja
    // before JS tries to assess its content.
    setTimeout(() => {
        updateStudentListView();
        console.log("JS: editST.js (overview page) initialized.");
    }, 100); // 100ms might be enough, adjust if needed

});