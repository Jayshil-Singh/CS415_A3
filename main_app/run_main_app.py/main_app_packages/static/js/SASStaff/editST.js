document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noStudentsMessage = document.getElementById('no-students-message');
    const studentTableContainer = document.getElementById('student-table-container');
    const studentsTableBody = document.getElementById('students-table-body');

    // Delete Confirmation Dialog Elements - Check if they exist
    const confirmationDialog = document.getElementById('confirmation-dialog');
    const dialogTitle = document.getElementById('dialog-title');
    const dialogMessage = document.getElementById('dialog-message');
    const cancelDeleteButton = document.getElementById('cancel-delete-button');
    const confirmDeleteButton = document.getElementById('confirm-delete-button');
    const snackbar = document.getElementById('snackbar');

    // Early exit if critical dialog elements are missing
    if (!confirmationDialog || !dialogMessage || !cancelDeleteButton || !confirmDeleteButton) {
        console.error("Delete confirmation dialog elements not found in the DOM. Deletion will not work.");
        // Optionally, you could disable delete buttons or show a persistent error message on the page.
    }
    if (!snackbar) {
        console.warn("Snackbar element not found. Notifications will not be shown.");
    }


    let studentIdToDelete = null;
    let studentNameToDelete = ""; // To store the name for the dialog message

    // --- ViewModel Simulation ---
    const viewModel = {
        students: [],
        isLoading: true,

        fetchStudents: async function() {
            this.isLoading = true;
            updateUIStates();
            return new Promise((resolve) => {
                setTimeout(() => {
                    this.students = [
                        { id: 'S1001', firstName: 'John', middleName: 'A.', lastName: 'Doe', address: '123 Main St, Suva', contact: '679-1234567', dateOfBirth: '1998-05-15', gender: 'Male', citizenship: 'Fijian', subprogram: 'Software Eng.', program: 'BSc IT', studentLevel: 'Year 2', campus: 'Main Campus' },
                        { id: 'S1002', firstName: 'Jane', middleName: '', lastName: 'Smith', address: '456 Market Rd, Nadi', contact: '679-9876543', dateOfBirth: '1999-02-20', gender: 'Female', citizenship: 'Fijian', subprogram: 'Networking', program: 'BSc IT', studentLevel: 'Year 3', campus: 'Lautoka Campus' },
                        { id: 'S1003', firstName: 'Peter', middleName: 'K.', lastName: 'Jones', address: '789 Queen St, Labasa', contact: '679-1122334', dateOfBirth: '2000-11-30', gender: 'Male', citizenship: 'Fijian', subprogram: 'Management', program: 'Dip Business', studentLevel: 'Year 1', campus: 'Labasa Campus' },
                    ];
                    this.isLoading = false;
                    resolve();
                }, 1500);
            });
        },

        deleteStudent: async function(studentId) {
            console.log(`Attempting to delete student with ID: ${studentId}`);
            // In a real app, this would be an API call to your Flask backend
            // For example:
            // try {
            //     const response = await fetch(`/api/delete-student/${studentId}`, { method: 'DELETE' });
            //     if (!response.ok) {
            //         const errorData = await response.json();
            //         throw new Error(errorData.error || 'Failed to delete student from server.');
            //     }
            //     const data = await response.json();
            //     this.students = this.students.filter(student => student.id !== studentId); // Update local cache
            //     return data.message || "Student deleted successfully";
            // } catch (error) {
            //     console.error("API Deletion error:", error);
            //     throw error; // Re-throw to be caught by the caller
            // }

            // Simulating API call
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
        }
    };

    // --- UI Update Functions ---
    function updateUIStates() {
        if (loadingIndicator) loadingIndicator.style.display = viewModel.isLoading ? 'block' : 'none';
        
        if (!viewModel.isLoading) {
            if (noStudentsMessage) noStudentsMessage.style.display = viewModel.students.length === 0 ? 'block' : 'none';
            if (studentTableContainer) studentTableContainer.style.display = viewModel.students.length > 0 ? 'block' : 'none';
        } else {
            if (noStudentsMessage) noStudentsMessage.style.display = 'none';
            if (studentTableContainer) studentTableContainer.style.display = 'none';
        }
    }

    function renderStudentTable() {
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
            // Safely access properties, providing empty string as fallback
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
                console.log("Edit student:", student.id);
                showSnackbar(`Edit functionality for ${student.firstName} (ID: ${student.id}) not fully implemented yet.`);
                // TODO: Implement edit functionality (e.g., open an edit modal)
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

    function showSnackbar(message) {
        if (!snackbar) return;
        snackbar.textContent = message;
        snackbar.classList.add('show');
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000);
    }

    // --- Delete Confirmation Dialog Logic ---
    function showDeleteConfirmationDialog(studentId, studentName) {
        if (!confirmationDialog || !dialogMessage) {
            console.error("Cannot show delete confirmation: dialog elements missing.");
            return;
        }
        studentIdToDelete = studentId;
        studentNameToDelete = studentName || "this student"; // Fallback name
        dialogMessage.textContent = `Are you sure you want to delete ${studentNameToDelete} (ID: ${studentIdToDelete})?`;
        if (dialogTitle) dialogTitle.textContent = "Confirm Deletion";
        confirmationDialog.style.display = 'flex'; // Explicitly set display to flex (or block)
        confirmationDialog.classList.add('show'); // Add .show for other styles like opacity if used
    }

    function hideDeleteConfirmationDialog() {
        if (!confirmationDialog) return;
        confirmationDialog.style.display = 'none'; // Explicitly hide
        confirmationDialog.classList.remove('show');
        studentIdToDelete = null;
        studentNameToDelete = "";
    }

    // --- Event Listeners ---
    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener('click', () => {
            hideDeleteConfirmationDialog();
        });
    }

    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', async () => {
            if (studentIdToDelete) {
                confirmDeleteButton.disabled = true;
                confirmDeleteButton.textContent = 'Deleting...';
                try {
                    const message = await viewModel.deleteStudent(studentIdToDelete);
                    showSnackbar(message);
                    // After successful deletion from backend (simulated or real),
                    // re-fetch the student list to reflect changes.
                    // Or, if deleteStudent updates the local viewModel.students directly,
                    // just re-rendering is fine for the simulation.
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
    
    if (confirmationDialog) {
        confirmationDialog.addEventListener('click', (event) => {
            if (event.target === confirmationDialog) { 
                hideDeleteConfirmationDialog();
            }
        });
    }

    // --- Initial Load ---
    async function initializePage() {
        await viewModel.fetchStudents();
        renderStudentTable();
    }

    // Ensure critical elements for the page to function are present before initializing
    if (studentsTableBody && loadingIndicator && noStudentsMessage && studentTableContainer && confirmationDialog) {
        initializePage();
    } else {
        console.error("One or more critical page elements for editST.js are missing. Page initialization skipped or incomplete.");
    }
});
