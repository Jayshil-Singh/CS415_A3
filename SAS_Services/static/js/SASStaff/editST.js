document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noStudentsMessage = document.getElementById('no-students-message');
    const studentTableContainer = document.getElementById('student-table-container');
    const studentsTableBody = document.getElementById('students-table-body');

    // Delete Confirmation Dialog Elements
    const confirmationDialog = document.getElementById('confirmation-dialog');
    const dialogTitle = document.getElementById('dialog-title');
    const dialogMessage = document.getElementById('dialog-message');
    const cancelDeleteButton = document.getElementById('cancel-delete-button');
    const confirmDeleteButton = document.getElementById('confirm-delete-button');
    
    // Edit Student Modal Elements
    const editStudentModal = document.getElementById('edit-student-modal');
    const editStudentForm = document.getElementById('edit-student-form');
    const cancelEditButton = document.getElementById('cancel-edit-button');
    const saveChangesButton = document.getElementById('save-changes-button'); // Get reference to the save button
    // Edit form fields
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

    // --- NEW: Confirm Save Changes Modal Elements ---
    const confirmSaveDialog = document.getElementById('confirm-save-dialog');
    const cancelSaveConfirmationButton = document.getElementById('cancel-save-confirmation-button');
    const confirmSaveFinalButton = document.getElementById('confirm-save-final-button');

    const snackbar = document.getElementById('snackbar');

    // Early exits if critical elements are missing
    if (!confirmationDialog || !dialogMessage || !cancelDeleteButton || !confirmDeleteButton) {
        console.error("Delete confirmation dialog elements not found.");
    }
    if (!editStudentModal || !editStudentForm || !cancelEditButton || !saveChangesButton) {
        console.error("Edit student modal elements not found.");
    }
    if (!confirmSaveDialog || !cancelSaveConfirmationButton || !confirmSaveFinalButton) {
        console.error("Save changes confirmation dialog elements not found.");
    }
    if (!snackbar) {
        console.warn("Snackbar element not found.");
    }

    let studentIdToDelete = null;
    let studentNameToDelete = ""; 
    let currentEditingStudent = null; 
    let currentEditFormData = null; // To store validated form data before final save confirmation

    // --- ViewModel Simulation ---
    const viewModel = {
        students: [],
        isLoading: true,
        fetchStudents: async function() { /* ... (same as before) ... */ 
            this.isLoading = true;
            updateUIStates();
            return new Promise((resolve) => {
                setTimeout(() => {
                    this.students = [
                        { id: 'S1001', firstName: 'John', middleName: 'A.', lastName: 'Doe', address: '123 Main St, Suva', contact: '679-1234567', dateOfBirth: '1998-05-15', gender: 'Male', citizenship: 'Fijian', subprogram: 'Software Eng.', program: 'BSc IT', studentLevel: 'Year 2', campus: 'Laucala Campus' },
                        { id: 'S1002', firstName: 'Jane', middleName: '', lastName: 'Smith', address: '456 Market Rd, Nadi', contact: '679-9876543', dateOfBirth: '1999-02-20', gender: 'Female', citizenship: 'Fijian', subprogram: 'Networking', program: 'BSc IT', studentLevel: 'Year 3', campus: 'Lautoka Campus' },
                        { id: 'S1003', firstName: 'Peter', middleName: 'K.', lastName: 'Jones', address: '789 Queen St, Labasa', contact: '679-1122334', dateOfBirth: '2000-11-30', gender: 'Male', citizenship: 'Fijian', subprogram: 'Management', program: 'Dip Business', studentLevel: 'Year 1', campus: 'Labasa Campus' },
                    ];
                    this.isLoading = false;
                    resolve();
                }, 1500);
            });
        },
        deleteStudent: async function(studentId) { /* ... (same as before) ... */ 
            console.log(`Attempting to delete student with ID: ${studentId}`);
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    const initialLength = this.students.length;
                    this.students = this.students.filter(student => student.id !== studentId);
                    if (this.students.length < initialLength) {
                        resolve("Student deleted successfully (simulated)");
                    } else {
                        reject("Student not found or could not be deleted (simulated).");
                    }
                }, 1000);
            });
        },
        updateStudent: async function(studentId, updatedData) { /* ... (same as before) ... */ 
            console.log(`Attempting to update student ID: ${studentId} with data:`, updatedData);
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    const studentIndex = this.students.findIndex(s => s.id === studentId);
                    if (studentIndex !== -1) {
                        this.students[studentIndex] = { ...this.students[studentIndex], ...updatedData, id: studentId }; 
                        resolve("Student updated successfully (simulated)");
                    } else {
                        reject("Student not found for update (simulated).");
                    }
                }, 1000);
            });
        }
    };

    // --- UI Update Functions ---
    function updateUIStates() { /* ... (same as before) ... */ 
        if (loadingIndicator) loadingIndicator.style.display = viewModel.isLoading ? 'block' : 'none';
        if (!viewModel.isLoading) {
            if (noStudentsMessage) noStudentsMessage.style.display = viewModel.students.length === 0 ? 'block' : 'none';
            if (studentTableContainer) studentTableContainer.style.display = viewModel.students.length > 0 ? 'block' : 'none';
        } else {
            if (noStudentsMessage) noStudentsMessage.style.display = 'none';
            if (studentTableContainer) studentTableContainer.style.display = 'none';
        }
    }
    function renderStudentTable() { /* ... (same as before, calls showEditModal) ... */ 
        if (!studentsTableBody) {
            console.error("studentsTableBody element not found. Cannot render table.");
            return;
        }
        studentsTableBody.innerHTML = ''; 

        if (viewModel.students.length === 0 && !viewModel.isLoading) {
            updateUIStates(); 
            return;
        }

        viewModel.students.forEach(student => {
            const row = studentsTableBody.insertRow();
            row.insertCell().textContent = student.id || '';
            row.insertCell().textContent = student.firstName || '';
            row.insertCell().textContent = student.middleName || '';
            row.insertCell().textContent = student.lastName || '';
            row.insertCell().textContent = student.address || '';
            row.insertCell().textContent = student.contact || '';
            row.insertCell().textContent = student.dateOfBirth || '';
            row.insertCell().textContent = student.gender || '';
            row.insertCell().textContent = student.citizenship || '';
            row.insertCell().textContent = student.subprogram || '';
            row.insertCell().textContent = student.program || '';
            row.insertCell().textContent = student.studentLevel || '';
            row.insertCell().textContent = student.campus || '';

            const actionsCell = row.insertCell();
            
            const editButton = document.createElement('button');
            editButton.innerHTML = '<span class="material-icons">edit</span>';
            editButton.classList.add('action-button', 'edit');
            editButton.title = "Edit Student";
            editButton.onclick = () => {
                showEditModal(student);
            };
            actionsCell.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.innerHTML = '<span class="material-icons">delete</span>';
            deleteButton.classList.add('action-button', 'delete');
            deleteButton.title = "Delete Student";
            deleteButton.onclick = () => {
                showDeleteConfirmationDialog(student.id, `${student.firstName || ''} ${student.lastName || ''}`.trim());
            };
            actionsCell.appendChild(deleteButton);
        });
        updateUIStates();
    }
    function showSnackbar(message) { /* ... (same as before) ... */ 
        if (!snackbar) return;
        snackbar.textContent = message;
        snackbar.classList.add('show');
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000);
    }

    // --- Delete Confirmation Dialog Logic ---
    function showDeleteConfirmationDialog(studentId, studentName) { /* ... (same as before) ... */ 
        if (!confirmationDialog || !dialogMessage) return;
        studentIdToDelete = studentId;
        studentNameToDelete = studentName || "this student";
        dialogMessage.textContent = `Are you sure you want to delete ${studentNameToDelete} (ID: ${studentIdToDelete})?`;
        if (dialogTitle) dialogTitle.textContent = "Confirm Deletion";
        confirmationDialog.style.display = 'flex';
        confirmationDialog.classList.add('show');
    }
    function hideDeleteConfirmationDialog() { /* ... (same as before) ... */ 
        if (!confirmationDialog) return;
        confirmationDialog.style.display = 'none';
        confirmationDialog.classList.remove('show');
        studentIdToDelete = null;
        studentNameToDelete = "";
    }

    // --- Edit Student Modal Logic ---
    function showEditModal(student) { /* ... (same as before) ... */ 
        if (!editStudentModal || !editStudentForm) return;
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

        editStudentModal.style.display = 'flex';
        editStudentModal.classList.add('show');
    }
    function hideEditModal() { /* ... (same as before) ... */ 
        if (!editStudentModal) return;
        editStudentModal.style.display = 'none';
        editStudentModal.classList.remove('show');
        if (editStudentForm) editStudentForm.reset(); 
        currentEditingStudent = null;
        currentEditFormData = null; // Clear pending form data
    }
    function validateEditFormField(inputElement) { /* ... (same as before) ... */ 
        if (!inputElement) return true;
        const errorElement = inputElement.closest('.form-group')?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";
        if (inputElement.required && !String(inputElement.value).trim()) {
            isValid = false;
            errorMessage = "This field is required.";
        }
        if (errorElement) errorElement.textContent = errorMessage;
        inputElement.classList.toggle('invalid', !isValid);
        return isValid;
    }
    function validateEditForm() { /* ... (same as before) ... */ 
        let isFormValid = true;
        if(editStudentForm){
            editStudentForm.querySelectorAll('input[required], select[required]').forEach(input => {
                if (!validateEditFormField(input)) {
                    isFormValid = false;
                }
            });
        }
        return isFormValid;
    }

    // --- NEW: Confirm Save Changes Dialog Logic ---
    function showConfirmSaveChangesDialog(formData) {
        if (!confirmSaveDialog) {
            console.error("Confirm save dialog element not found.");
            // Fallback to direct save if dialog is missing, or handle error appropriately
            processSaveChanges(formData); 
            return;
        }
        currentEditFormData = formData; // Store the data that passed edit form validation
        confirmSaveDialog.style.display = 'flex';
        confirmSaveDialog.classList.add('show');
    }

    function hideConfirmSaveChangesDialog() {
        if (!confirmSaveDialog) return;
        confirmSaveDialog.style.display = 'none';
        confirmSaveDialog.classList.remove('show');
        // Don't clear currentEditFormData here, it's needed if user confirms. Clear it after processing or if edit is cancelled.
    }

    async function processSaveChanges(formData) {
        if (!currentEditingStudent || !currentEditingStudent.id || !formData) {
            showSnackbar("Error: No student or data to save.", false);
            return;
        }

        if(saveChangesButton) {
            saveChangesButton.disabled = true;
            saveChangesButton.textContent = 'Saving...';
        }

        try {
            const message = await viewModel.updateStudent(currentEditingStudent.id, formData);
            showSnackbar(message);
            hideEditModal(); // Hide the main edit modal after successful save
            renderStudentTable();
        } catch (error) {
            showSnackbar(String(error) || "Error updating student.", false);
            console.error("Update error:", error);
        } finally {
            currentEditFormData = null; // Clear the stored form data
            if(saveChangesButton) {
                saveChangesButton.disabled = false;
                saveChangesButton.textContent = 'Save Changes';
            }
        }
    }

    // --- Event Listeners ---
    // Delete confirmation
    if (cancelDeleteButton) { cancelDeleteButton.addEventListener('click', hideDeleteConfirmationDialog); }
    if (confirmDeleteButton) { /* ... (same as before, calls hideDeleteConfirmationDialog) ... */ 
        confirmDeleteButton.addEventListener('click', async () => {
            if (studentIdToDelete) {
                confirmDeleteButton.disabled = true;
                confirmDeleteButton.textContent = 'Deleting...';
                try {
                    const message = await viewModel.deleteStudent(studentIdToDelete);
                    showSnackbar(message);
                    renderStudentTable(); 
                } catch (error) {
                    showSnackbar(String(error) || "Error deleting student.");
                    console.error("Deletion error:", error);
                } finally {
                    hideDeleteConfirmationDialog();
                    confirmDeleteButton.disabled = false;
                    confirmDeleteButton.textContent = 'Delete';
                }
            }
        });
    }
    if (confirmationDialog) { confirmationDialog.addEventListener('click', (event) => { if (event.target === confirmationDialog) hideDeleteConfirmationDialog(); }); }

    // Edit Modal
    if (cancelEditButton) { cancelEditButton.addEventListener('click', hideEditModal); }
    if (editStudentForm) {
        editStudentForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (!currentEditingStudent) return;

            if (validateEditForm()) {
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
                // Instead of direct save, show the confirm save dialog
                showConfirmSaveChangesDialog(updatedDataFromForm);
            } else {
                showSnackbar("Please correct the errors in the edit form.", false);
            }
        });
    }
    if (editStudentModal) { editStudentModal.addEventListener('click', (event) => { if (event.target === editStudentModal) hideEditModal(); }); }

    // --- NEW: Event Listeners for Confirm Save Changes Modal ---
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
            if (currentEditFormData) { // If there's data pending confirmation
                processSaveChanges(currentEditFormData);
            }
        });
    }

    if (confirmSaveDialog) {
        confirmSaveDialog.addEventListener('click', (event) => {
            if (event.target === confirmSaveDialog) { // Clicked on overlay
                hideConfirmSaveChangesDialog();
                // Re-enable save changes button in edit modal
                if (saveChangesButton) {
                    saveChangesButton.disabled = false;
                    saveChangesButton.textContent = 'Save Changes';
                }
            }
        });
    }

    // --- Initial Load ---
    async function initializePage() { /* ... (same as before) ... */ 
        await viewModel.fetchStudents();
        renderStudentTable();
    }
    if (studentsTableBody && loadingIndicator && noStudentsMessage && studentTableContainer && confirmationDialog && editStudentModal && confirmSaveDialog) {
        initializePage();
    } else {
        console.error("One or more critical page elements for editST.js are missing. Page initialization skipped or incomplete.");
    }
});
