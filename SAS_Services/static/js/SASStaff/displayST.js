// static/js/SASStaff/displayST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("displayST.js: DOMContentLoaded");

    const editStudentBtn = document.getElementById('edit-student-details-btn');
    const disableStudentBtn = document.getElementById('disable-student-btn');
    const studentId = editStudentBtn ? editStudentBtn.dataset.id : null; // Or get from URL/hidden field

    if (editStudentBtn) {
        editStudentBtn.addEventListener('click', () => {
            if (!studentId) {
                console.error("Student ID not found for editing.");
                return;
            }
            console.log(`Edit button clicked for student ID: ${studentId}`);
            alert(`Mock: Opening edit form for student ${studentId}. You would typically open an edit modal or redirect to an edit page here.`);
            // TODO: Implement opening an edit modal or navigating to an edit page
            // You could re-use/adapt the #edit-student-modal from the old editST.html
            // and its associated form handling logic here.
        });
    }

    if (disableStudentBtn) {
        disableStudentBtn.addEventListener('click', () => {
            if (!studentId) {
                console.error("Student ID not found for disabling.");
                return;
            }
            console.log(`Disable button clicked for student ID: ${studentId}`);
            // TODO: Implement a custom confirmation modal
            const confirmDisable = confirm(`Are you sure you want to disable student ${studentId}? This action might be irreversible.`);
            if (confirmDisable) {
                alert(`Mock: Disabling student ${studentId}. You would make an API call here.`);
                // TODO: Make an API call to disable the student
                // On success, you might want to redirect or update the UI (e.g., show a "Disabled" status)
            }
        });
    }

    console.log("displayST.js: Initialized.");
});