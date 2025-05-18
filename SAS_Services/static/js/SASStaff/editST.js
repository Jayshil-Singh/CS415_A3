// static/js/SASStaff/editST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("editST.js: DOMContentLoaded");

    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noStudentsMessage = document.getElementById('no-students-message');
    const studentTableContainer = document.getElementById('student-table-container');
    const studentsTableBody = document.getElementById('students-table-body');

    // Delete Confirmation Dialog Elements
    const deleteConfirmationDialog = document.getElementById('delete-confirmation-dialog'); // Corrected ID from your HTML
    // const dialogTitle = document.getElementById('dialog-title'); // This ID is generic, ensure it's the correct one for delete
    const deleteDialogTitle = document.getElementById('delete-dialog-title'); // Specific ID from your HTML
    const deleteDialogMessage = document.getElementById('delete-dialog-message'); // Specific ID
    const cancelDeleteButton = document.getElementById('cancel-delete-button');
    const confirmDeleteButton = document.getElementById('confirm-delete-button');
    
    // Edit Student Modal Elements
    const editStudentModal = document.getElementById('edit-student-modal');
    const editStudentForm = document.getElementById('edit-student-form');
    const cancelEditButton = document.getElementById('cancel-edit-button');
    const saveChangesButton = document.getElementById('save-changes-button');
    
    // Edit form fields (ensure all these IDs exist in your edit modal form)
    const editStudentIdInput = document.getElementById('edit-student-id');
    const editFirstNameInput = document.getElementById('edit-first-name');
    const editMiddleNameInput = document.getElementById('edit-middle-name');
    const editLastNameInput = document.getElementById('edit-last-name');
    const editAddressInput = document.getElementById('edit-address');
    const editContactInput = document.getElementById('edit-contact');
    const editDobInput = document.getElementById('edit-date-of-birth');
    const editGenderSelect = document.getElementById('edit-gender');
    const editCitizenshipInput = document.getElementById('edit-citizenship');
    const editProgramInput = document.getElementById('edit-program');
    const editSubprogramInput = document.getElementById('edit-subprogram');
    const editStudentLevelInput = document.getElementById('edit-student-level');
    const editCampusInput = document.getElementById('edit-campus');

    // Confirm Save Changes Modal Elements
    const confirmSaveDialog = document.getElementById('confirm-save-dialog');
    const cancelSaveConfirmationButton = document.getElementById('cancel-save-confirmation-button');
    const confirmSaveFinalButton = document.getElementById('confirm-save-final-button');

    const snackbar = document.getElementById('snackbar');

    // Check critical elements
    if (!loadingIndicator || !noStudentsMessage || !studentTableContainer || !studentsTableBody) {
        console.error("JS FATAL: Core page structure elements (loading, table container, etc.) are missing!");
        if(loadingIndicator) loadingIndicator.innerHTML = "<p>Error: Page structure incomplete. Cannot load student data.</p>";
        return; // Stop further execution if these are missing
    }
    console.log("JS: Core page structure elements found.");


    let studentIdToDelete = null;
    let studentNameToDelete = ""; 
    let currentEditingStudent = null; 
    let currentEditFormData = null;

    // --- ViewModel ---
    const viewModel = {
        students: [], // Will be populated by fetchStudents
        isLoading: true,

        fetchStudents: async function() {
            console.log("JS: viewModel.fetchStudents - Starting to fetch (mock)...");
            this.isLoading = true;
            updateUIStates(); // Show loader, hide table/message
            
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Mock data (this will replace any HTML dummy data if renderStudentTable clears the tbody)
                    this.students = [
                        { id: 'S1001', firstName: 'John (JS)', middleName: 'A.', lastName: 'Doe', address: '123 Main St, Suva', contact: '679-1234567', dateOfBirth: '1998-05-15', gender: 'Male', citizenship: 'Fijian', subprogram: 'Software Eng.', program: 'BSc IT', studentLevel: 'Year 2', campus: 'Laucala Campus' },
                        { id: 'S1002', firstName: 'Jane (JS)', middleName: '', lastName: 'Smith', address: '456 Market Rd, Nadi', contact: '679-9876543', dateOfBirth: '1999-02-20', gender: 'Female', citizenship: 'Fijian', subprogram: 'Networking', program: 'BSc IT', studentLevel: 'Year 3', campus: 'Lautoka Campus' },
                        { id: 'S1003', firstName: 'Peter (JS)', middleName: 'K.', lastName: 'Jones', address: '789 Queen St, Labasa', contact: '679-1122334', dateOfBirth: '2000-11-30', gender: 'Male', citizenship: 'Fijian', subprogram: 'Management', program: 'Dip Business', studentLevel: 'Year 1', campus: 'Labasa Campus' },
                    ];
                    this.isLoading = false;
                    console.log("JS: viewModel.fetchStudents - Mock data fetched:", this.students);
                    resolve(); // Resolve after updating students
                }, 1500); // Simulate network delay
            });
        },

        deleteStudent: async function(studentId) { 
            console.log(`JS: viewModel.deleteStudent - Attempting to delete student ID: ${studentId}`);
            // In a real app, this would be an API call to the backend.
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    const initialLength = this.students.length;
                    this.students = this.students.filter(student => student.id !== studentId);
                    if (this.students.length < initialLength) {
                        console.log("JS: viewModel.deleteStudent - Success (mock).");
                        resolve("Student deleted successfully (simulated).");
                    } else {
                        console.warn("JS: viewModel.deleteStudent - Failure, student not found (mock).");
                        reject("Student not found or could not be deleted (simulated).");
                    }
                }, 800);
            });
        },

        updateStudent: async function(studentId, updatedData) { 
            console.log(`JS: viewModel.updateStudent - Attempting to update student ID: ${studentId} with data:`, updatedData);
            // In a real app, this would be an API call.
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    const studentIndex = this.students.findIndex(s => s.id === studentId);
                    if (studentIndex !== -1) {
                        this.students[studentIndex] = { ...this.students[studentIndex], ...updatedData, id: studentId }; 
                        console.log("JS: viewModel.updateStudent - Success (mock). Student data:", this.students[studentIndex]);
                        resolve("Student updated successfully (simulated).");
                    } else {
                        console.warn("JS: viewModel.updateStudent - Failure, student not found (mock).");
                        reject("Student not found for update (simulated).");
                    }
                }, 800);
            });
        }
    };

    // --- UI Update Functions ---
    function updateUIStates() {
        console.log("JS: updateUIStates called. isLoading:", viewModel.isLoading, "students.length:", viewModel.students.length);
        if (loadingIndicator) loadingIndicator.style.display = viewModel.isLoading ? 'block' : 'none';
        
        if (!viewModel.isLoading) {
            if (viewModel.students.length > 0) {
                if (studentTableContainer) studentTableContainer.style.display = 'block'; // Or 'flex' if CSS expects it
                if (noStudentsMessage) noStudentsMessage.style.display = 'none';
                console.log("JS: Showing student table.");
            } else {
                if (studentTableContainer) studentTableContainer.style.display = 'none';
                if (noStudentsMessage) noStudentsMessage.style.display = 'block';
                console.log("JS: Showing 'no students' message.");
            }
        } else { // Still loading
            if (studentTableContainer) studentTableContainer.style.display = 'none';
            if (noStudentsMessage) noStudentsMessage.style.display = 'none';
            console.log("JS: Still loading, table and 'no students' message hidden.");
        }
    }

    function renderStudentTable() {
        console.log("JS: renderStudentTable called.");
        if (!studentsTableBody) {
            console.error("JS ERROR: studentsTableBody element not found. Cannot render table.");
            return;
        }
        studentsTableBody.innerHTML = ''; // Clear previous content (including HTML dummy data)

        if (viewModel.students.length === 0) {
            console.log("JS: No students to render in table.");
            updateUIStates(); // Ensure correct message (no students or loader) is shown
            return;
        }

        viewModel.students.forEach(student => {
            const row = studentsTableBody.insertRow();
            // Safely access properties with fallbacks
            row.insertCell().textContent = student.id || 'N/A';
            row.insertCell().textContent = student.firstName || 'N/A';
            row.insertCell().textContent = student.middleName || ''; // Middle name can be empty
            row.insertCell().textContent = student.lastName || 'N/A';
            row.insertCell().textContent = student.address || 'N/A';
            row.insertCell().textContent = student.contact || 'N/A';
            row.insertCell().textContent = student.dateOfBirth || 'N/A';
            row.insertCell().textContent = student.gender || 'N/A';
            row.insertCell().textContent = student.citizenship || 'N/A';
            row.insertCell().textContent = student.subprogram || 'N/A';
            row.insertCell().textContent = student.program || 'N/A';
            row.insertCell().textContent = student.studentLevel || 'N/A';
            row.insertCell().textContent = student.campus || 'N/A';

            const actionsCell = row.insertCell();
            
            const editButton = document.createElement('button');
            editButton.innerHTML = '<span class="material-icons">edit</span>';
            editButton.classList.add('action-button', 'edit-btn'); // Matched class from your HTML dummy data
            editButton.title = `Edit ${student.firstName} ${student.lastName}`;
            editButton.setAttribute('data-id', student.id);
            editButton.setAttribute('aria-label', `Edit ${student.firstName} ${student.lastName}`);
            editButton.onclick = () => showEditModal(student);
            actionsCell.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.innerHTML = '<span class="material-icons">delete</span>';
            deleteButton.classList.add('action-button', 'delete-btn'); // Matched class from your HTML dummy data
            deleteButton.title = `Delete ${student.firstName} ${student.lastName}`;
            deleteButton.setAttribute('data-id', student.id);
            deleteButton.setAttribute('aria-label', `Delete ${student.firstName} ${student.lastName}`);
            deleteButton.onclick = () => showDeleteConfirmationDialog(student.id, `${student.firstName || ''} ${student.lastName || ''}`.trim());
            actionsCell.appendChild(deleteButton);
        });
        updateUIStates(); // Ensure table container is visible
        console.log("JS: Student table rendered with data.");
    }
    
    function showSnackbar(message, isSuccess = true) {
        if (!snackbar) {
            console.warn("JS WARN: Snackbar element not found. Using alert fallback.");
            alert(message);
            return;
        }
        snackbar.textContent = message;
        snackbar.className = 'snackbar'; // Reset classes
        snackbar.classList.add(isSuccess ? 'success' : 'error'); // Optional: for styling
        snackbar.classList.add('show'); // Trigger CSS animation
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000);
    }

    // --- Modal Control & Logic ---
    function showModal(modalElement) {
        if (!modalElement) return;
        modalElement.style.display = 'flex';
        setTimeout(() => modalElement.classList.add('active'), 10); // Use 'active' for CSS transitions
    }

    function hideModal(modalElement) {
        if (!modalElement) return;
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) {
                modalElement.style.display = 'none';
            }
        }, 300); // Match CSS transition duration
    }

    // Delete Confirmation Dialog
    function showDeleteConfirmationDialog(studentId, studentName) {
        if (!deleteConfirmationDialog || !deleteDialogMessage || !deleteDialogTitle) {
            console.error("JS Error: Delete confirmation dialog elements missing.");
            return;
        }
        studentIdToDelete = studentId;
        studentNameToDelete = studentName || "this student";
        deleteDialogMessage.textContent = `Are you sure you want to delete ${studentNameToDelete} (ID: ${studentIdToDelete})?`;
        deleteDialogTitle.textContent = "Confirm Deletion"; // Set title if it's generic
        showModal(deleteConfirmationDialog);
    }
    function hideDeleteConfirmationDialog() {
        hideModal(deleteConfirmationDialog);
        studentIdToDelete = null;
        studentNameToDelete = "";
    }

    // Edit Student Modal
    function showEditModal(student) {
        if (!editStudentModal || !editStudentForm) {
            console.error("JS Error: Edit student modal or form not found.");
            return;
        }
        currentEditingStudent = student; 

        if(editStudentIdInput) editStudentIdInput.value = student.id || '';
        if(editFirstNameInput) editFirstNameInput.value = student.firstName || '';
        if(editMiddleNameInput) editMiddleNameInput.value = student.middleName || '';
        if(editLastNameInput) editLastNameInput.value = student.lastName || '';
        if(editAddressInput) editAddressInput.value = student.address || '';
        if(editContactInput) editContactInput.value = student.contact || '';
        if(editDobInput) editDobInput.value = student.dateOfBirth || '';
        if(editGenderSelect) editGenderSelect.value = student.gender || '';
        if(editCitizenshipInput) editCitizenshipInput.value = student.citizenship || '';
        if(editProgramInput) editProgramInput.value = student.program || '';
        if(editSubprogramInput) editSubprogramInput.value = student.subprogram || '';
        if(editStudentLevelInput) editStudentLevelInput.value = student.studentLevel || '';
        if(editCampusInput) editCampusInput.value = student.campus || '';

        editStudentForm.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        editStudentForm.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
        showModal(editStudentModal);
    }
    function hideEditModal() {
        if (!editStudentModal) return;
        hideModal(editStudentModal);
        if (editStudentForm) editStudentForm.reset(); 
        currentEditingStudent = null;
        currentEditFormData = null;
    }

    function validateEditFormField(inputElement) { 
        if (!inputElement) return true;
        const errorElement = inputElement.closest('.form-group')?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";
        if (inputElement.required && !String(inputElement.value).trim()) {
            isValid = false;
            errorMessage = "This field is required.";
        }
        // Add more specific validations here if needed (e.g., for email, phone format)
        if (errorElement) errorElement.textContent = errorMessage;
        inputElement.classList.toggle('invalid', !isValid);
        return isValid;
    }
    function validateEditForm() { 
        let isFormValid = true;
        if(editStudentForm){
            editStudentForm.querySelectorAll('input[required], select[required]').forEach(input => {
                if (!validateEditFormField(input)) {
                    isFormValid = false;
                }
            });
        } else {
            isFormValid = false; // Form not found
        }
        return isFormValid;
    }

    // Confirm Save Changes Dialog
    function showConfirmSaveChangesDialog(formData) {
        if (!confirmSaveDialog) {
            console.error("JS Error: Confirm save dialog element not found. Saving directly (mock).");
            processSaveChanges(formData); 
            return;
        }
        currentEditFormData = formData; 
        showModal(confirmSaveDialog);
    }

    function hideConfirmSaveChangesDialog() {
        if (!confirmSaveDialog) return;
        hideModal(confirmSaveDialog);
    }

    async function processSaveChanges(formData) {
        if (!currentEditingStudent || !currentEditingStudent.id || !formData) {
            showSnackbar("Error: No student data to save.", false);
            return;
        }

        if(saveChangesButton) {
            saveChangesButton.disabled = true;
            saveChangesButton.textContent = 'Saving...';
        }

        try {
            const message = await viewModel.updateStudent(currentEditingStudent.id, formData);
            showSnackbar(message, true);
            hideEditModal(); 
            renderStudentTable(); // Re-render table with updated data
        } catch (error) {
            showSnackbar(String(error) || "Error updating student.", false);
            console.error("Update error:", error);
        } finally {
            currentEditFormData = null; 
            if(saveChangesButton) {
                saveChangesButton.disabled = false;
                saveChangesButton.textContent = 'Save Changes';
            }
        }
    }

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        console.log("JS: Setting up event listeners...");
        // Delete confirmation
        if (cancelDeleteButton) cancelDeleteButton.addEventListener('click', hideDeleteConfirmationDialog);
        if (confirmDeleteButton) {
            confirmDeleteButton.addEventListener('click', async () => {
                if (studentIdToDelete) {
                    confirmDeleteButton.disabled = true;
                    confirmDeleteButton.textContent = 'Deleting...';
                    try {
                        const message = await viewModel.deleteStudent(studentIdToDelete);
                        showSnackbar(message, true);
                        renderStudentTable(); 
                    } catch (error) {
                        showSnackbar(String(error) || "Error deleting student.", false);
                    } finally {
                        hideDeleteConfirmationDialog();
                        confirmDeleteButton.disabled = false;
                        confirmDeleteButton.textContent = 'Delete';
                    }
                }
            });
        }
        if (deleteConfirmationDialog) { 
            deleteConfirmationDialog.addEventListener('click', (event) => { 
                if (event.target === deleteConfirmationDialog) hideDeleteConfirmationDialog(); 
            }); 
        }

        // Edit Modal
        if (cancelEditButton) cancelEditButton.addEventListener('click', hideEditModal);
        if (editStudentForm) {
            editStudentForm.addEventListener('submit', (event) => {
                event.preventDefault();
                console.log("JS: Edit form submitted.");
                if (!currentEditingStudent) {
                    console.error("JS Error: currentEditingStudent is not set.");
                    return;
                }
                if (validateEditForm()) {
                    console.log("JS: Edit form is valid.");
                    const updatedDataFromForm = {
                        firstName: editFirstNameInput?.value,
                        middleName: editMiddleNameInput?.value,
                        lastName: editLastNameInput?.value,
                        address: editAddressInput?.value,
                        contact: editContactInput?.value,
                        dateOfBirth: editDobInput?.value,
                        gender: editGenderSelect?.value,
                        citizenship: editCitizenshipInput?.value,
                        program: editProgramInput?.value,
                        subprogram: editSubprogramInput?.value,
                        studentLevel: editStudentLevelInput?.value,
                        campus: editCampusInput?.value,
                    };
                    showConfirmSaveChangesDialog(updatedDataFromForm);
                } else {
                    console.warn("JS: Edit form validation failed.");
                    showSnackbar("Please correct the errors in the form.", false);
                }
            });
        }
        if (editStudentModal) { 
            editStudentModal.addEventListener('click', (event) => { 
                if (event.target === editStudentModal) hideEditModal(); 
            }); 
        }

        // Confirm Save Changes Modal
        if (cancelSaveConfirmationButton) {
            cancelSaveConfirmationButton.addEventListener('click', () => {
                hideConfirmSaveChangesDialog();
                // User wants to review, edit modal should still be open.
                // Re-enable save changes button in edit modal if it was disabled
                if (saveChangesButton) {
                    saveChangesButton.disabled = false;
                    saveChangesButton.textContent = 'Save Changes';
                }
            });
        }
        if (confirmSaveFinalButton) {
            confirmSaveFinalButton.addEventListener('click', () => {
                hideConfirmSaveChangesDialog();
                if (currentEditFormData) { 
                    processSaveChanges(currentEditFormData);
                } else {
                    console.warn("JS: No currentEditFormData to save.");
                }
            });
        }
        if (confirmSaveDialog) {
            confirmSaveDialog.addEventListener('click', (event) => {
                if (event.target === confirmSaveDialog) { 
                    hideConfirmSaveChangesDialog();
                    if (saveChangesButton) { // Also re-enable main save button
                        saveChangesButton.disabled = false;
                        saveChangesButton.textContent = 'Save Changes';
                    }
                }
            });
        }
        console.log("JS: Event listeners set up.");
    }

    // --- Initial Load ---
    async function initializePage() {
        console.log("JS: Initializing page...");
        await viewModel.fetchStudents(); // Fetches mock data into viewModel.students
        renderStudentTable();          // Renders table from viewModel.students
        // updateUIStates(); // Called at the end of fetchStudents and renderStudentTable
        console.log("JS: Page initialized and table rendered.");
    }

    // Check if all essential elements are present before initializing
    if (studentsTableBody && loadingIndicator && noStudentsMessage && studentTableContainer &&
        deleteConfirmationDialog && editStudentModal && confirmSaveDialog) {
        initializePage();
        setupEventListeners(); // Setup event listeners after elements are confirmed
    } else {
        console.error("JS FATAL: One or more critical page elements for editST.js are missing. Full initialization aborted.");
        if (loadingIndicator) loadingIndicator.innerHTML = "<p style='color:red;'>Error: Page components missing. Functionality will be limited.</p>";
    }
});