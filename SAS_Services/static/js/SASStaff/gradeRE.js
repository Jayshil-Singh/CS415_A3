// static/js/SASStaff/gradeRE.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("gradeRE.js: DOMContentLoaded");

    const loadingIndicator = document.getElementById('loading-indicator');
    const applicationsTableContainer = document.getElementById('applications-table-container');
    const noApplicationsMessage = document.getElementById('no-applications-message');
    const applicationsTableBody = document.getElementById('applications-table-body');

    // NEW: Rejection Info Modal elements
    const rejectionModal = document.getElementById('rejection-info-modal');
    const rejectionModalStudentIdSpan = document.getElementById('rejection-modal-student-id');
    const rejectionModalCourseCodeSpan = document.getElementById('rejection-modal-course-code');
    const rejectionModalOkBtn = document.getElementById('rejection-info-ok-btn');
    const rejectionModalCloseBtn = rejectionModal ? rejectionModal.querySelector('.modal-close-button') : null;

    // --- Modal show/hide utility functions (if not already in a global script) ---
    function showModal(modalElement) {
        if (!modalElement) {
            console.error("Attempted to show null modal:", modalElement);
            return;
        }
        modalElement.style.display = 'flex';
        setTimeout(() => modalElement.classList.add('active'), 10);
    }

    function hideModal(modalElement) {
        if (!modalElement) {
            console.error("Attempted to hide null modal:", modalElement);
            return;
        }
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) {
                modalElement.style.display = 'none';
            }
        }, 300); // Should match CSS transition duration
    }
    // --- End Modal utility functions ---

    function showLoading(isLoading) {
        if (loadingIndicator) {
            loadingIndicator.style.display = isLoading ? 'flex' : 'none'; // Use flex for centering
        }
    }

    function displayApplications() {
        console.log("JS: Displaying applications table or 'no applications' message.");
        showLoading(false);

        // Check if the tbody has actual data rows (not just the "No applications to display" row)
        const hasActualData = applicationsTableBody && applicationsTableBody.querySelector('td:not([colspan="8"])');

        if (hasActualData) {
            if (applicationsTableContainer) applicationsTableContainer.style.display = 'block';
            if (noApplicationsMessage) noApplicationsMessage.style.display = 'none';
        } else {
            if (applicationsTableContainer) applicationsTableContainer.style.display = 'none';
            if (noApplicationsMessage) noApplicationsMessage.style.display = 'block';
        }
    }

    // Simulate initial loading
    showLoading(true);
    setTimeout(() => {
        displayApplications();
    }, 500);

    // Event listeners for action buttons
    if (applicationsTableContainer) {
        applicationsTableContainer.addEventListener('click', function(event) {
            const target = event.target.closest('.action-button');
            if (!target) return;

            const studentId = target.dataset.id;
            const courseCode = target.dataset.course;
            const studentFullName = `${target.closest('tr')?.cells[1]?.textContent || ''} ${target.closest('tr')?.cells[2]?.textContent || ''}`.trim();


            if (target.classList.contains('approve-btn')) {
                console.log(`Approve clicked for Student ID: ${studentId}, Course: ${courseCode}`);
                // Redirect to the all students grades page
                // Assuming the URL is /sas-staff/all-students-grades as per your app.py
                // You might want to pass studentId and courseCode as query parameters if the target page needs to highlight this student/course
                // For example: window.location.href = `/sas-staff/all-students-grades?student_id=${studentId}&course_code=${courseCode}`;
                // For now, a simple redirect:
                alert(`Mock Approve Action: Student ${studentId}, Course ${courseCode}.\nRedirecting to All Student Grades page...`); // Temporary alert
                window.location.href = '/sas-staff/all-students-grades';

            } else if (target.classList.contains('reject-btn')) {
                console.log(`Reject clicked for Student ID: ${studentId}, Course: ${courseCode}`);

                if (rejectionModalStudentIdSpan) rejectionModalStudentIdSpan.textContent = studentId || 'N/A';
                if (rejectionModalCourseCodeSpan) rejectionModalCourseCodeSpan.textContent = courseCode || 'N/A';
                // You could customize the message further if needed
                // e.g., `rejectionInfoMessage.textContent = "Please email " + studentFullName + " (ID:..." `

                showModal(rejectionModal);
            }
        });
    }

    // NEW: Event listeners for Rejection Info Modal
    if (rejectionModalOkBtn) {
        rejectionModalOkBtn.addEventListener('click', () => hideModal(rejectionModal));
    }
    if (rejectionModalCloseBtn) {
        rejectionModalCloseBtn.addEventListener('click', () => hideModal(rejectionModal));
    }
    if (rejectionModal) { // Optional: close on backdrop click
        rejectionModal.addEventListener('click', (event) => {
            if (event.target === rejectionModal) {
                hideModal(rejectionModal);
            }
        });
    }

    console.log("gradeRE.js: Initialized and event listeners set up.");
});