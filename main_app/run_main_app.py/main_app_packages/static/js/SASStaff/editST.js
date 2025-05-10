document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noStudentsMessage = document.getElementById('no-students-message');
    const studentTableContainer = document.getElementById('student-table-container');
    const studentsTableBody = document.getElementById('students-table-body');

    const confirmationDialog = document.getElementById('confirmation-dialog');
    const dialogMessage = document.getElementById('dialog-message'); // If you want to customize message per student
    const cancelDeleteButton = document.getElementById('cancel-delete-button');
    const confirmDeleteButton = document.getElementById('confirm-delete-button');
    const snackbar = document.getElementById('snackbar');

    let studentIdToDelete = null;

    // --- ViewModel Simulation ---
    const viewModel = {
        students: [],
        isLoading: true,

        // Simulate fetching students (replace with actual API call)
        fetchStudents: async function() {
            this.isLoading = true;
            updateUIStates(); // Show loading indicator

            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    // Sample data - replace with actual data structure from your backend
                    this.students = [
                        { id: 'S1001', firstName: 'John', middleName: 'A.', lastName: 'Doe', address: '123 Main St, Suva', contact: '679-1234567', dateOfBirth: '1998-05-15', gender: 'Male', citizenship: 'Fijian', subprogram: 'Software Eng.', program: 'BSc IT', studentLevel: 'Year 2', campus: 'Main Campus' },
                        { id: 'S1002', firstName: 'Jane', middleName: '', lastName: 'Smith', address: '456 Market Rd, Nadi', contact: '679-9876543', dateOfBirth: '1999-02-20', gender: 'Female', citizenship: 'Fijian', subprogram: 'Networking', program: 'BSc IT', studentLevel: 'Year 3', campus: 'Lautoka Campus' },
                        { id: 'S1003', firstName: 'Peter', middleName: 'K.', lastName: 'Jones', address: '789 Queen St, Labasa', contact: '679-1122334', dateOfBirth: '2000-11-30', gender: 'Male', citizenship: 'Fijian', subprogram: 'Management', program: 'Dip Business', studentLevel: 'Year 1', campus: 'Labasa Campus' },
                    ];
                    this.isLoading = false;
                    resolve();
                }, 1500); // Simulate network delay
            });
        },

        // Simulate deleting a student
        deleteStudent: async function(studentId) {
            console.log(`Attempting to delete student with ID: ${studentId}`);
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    const initialLength = this.students.length;
                    this.students = this.students.filter(student => student.id !== studentId);
                    if (this.students.length < initialLength) {
                        resolve("Student deleted successfully");
                    } else {
                        reject("Student not found or could not be deleted.");
                    }
                }, 1000);
            });
        }
    };

    // --- UI Update Functions ---
    function updateUIStates() {
        loadingIndicator.style.display = viewModel.isLoading ? 'block' : 'none';
        
        if (!viewModel.isLoading) {
            noStudentsMessage.style.display = viewModel.students.length === 0 ? 'block' : 'none';
            studentTableContainer.style.display = viewModel.students.length > 0 ? 'block' : 'none';
        } else {
            noStudentsMessage.style.display = 'none';
            studentTableContainer.style.display = 'none';
        }
    }

    function renderStudentTable() {
        studentsTableBody.innerHTML = ''; // Clear existing rows

        if (viewModel.students.length === 0) {
            updateUIStates(); // Ensure "No students found" is shown
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
            // Edit button (placeholder for now)
            // const editButton = document.createElement('button');
            // editButton.innerHTML = '<span class="material-icons">edit</span>';
            // editButton.classList.add('action-button', 'edit');
            // editButton.title = "Edit Student";
            // editButton.onclick = () => {
            //     console.log("Edit student:", student.id);
            //     alert(`Edit functionality for ${student.firstName} (ID: ${student.id}) not implemented yet.`);
            // };
            // actionsCell.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.innerHTML = '<span class="material-icons">delete</span>';
            deleteButton.classList.add('action-button', 'delete');
            deleteButton.title = "Delete Student";
            deleteButton.onclick = () => {
                studentIdToDelete = student.id;
                // Optionally customize dialog message:
                // dialogMessage.textContent = `Are you sure you want to delete ${student.firstName} ${student.lastName} (ID: ${student.id})?`;
                confirmationDialog.classList.add('show');
            };
            actionsCell.appendChild(deleteButton);
        });
        updateUIStates(); // Update visibility based on new student list
    }

    function showSnackbar(message) {
        snackbar.textContent = message;
        snackbar.classList.add('show');
        setTimeout(() => {
            snackbar.classList.remove('show');
        }, 3000); // Snackbar visible for 3 seconds
    }

    // --- Event Listeners ---
    cancelDeleteButton.addEventListener('click', () => {
        confirmationDialog.classList.remove('show');
        studentIdToDelete = null;
    });

    confirmDeleteButton.addEventListener('click', async () => {
        if (studentIdToDelete) {
            confirmDeleteButton.disabled = true;
            confirmDeleteButton.textContent = 'Deleting...';
            try {
                const message = await viewModel.deleteStudent(studentIdToDelete);
                showSnackbar(message);
                renderStudentTable(); // Re-render table after deletion
            } catch (error) {
                showSnackbar(error || "Error deleting student.");
                console.error("Deletion error:", error);
            } finally {
                confirmationDialog.classList.remove('show');
                studentIdToDelete = null;
                confirmDeleteButton.disabled = false;
                confirmDeleteButton.textContent = 'Delete';
            }
        }
    });
    
    // Close modal if clicked outside the content (optional)
    confirmationDialog.addEventListener('click', (event) => {
        if (event.target === confirmationDialog) {
            confirmationDialog.classList.remove('show');
            studentIdToDelete = null;
        }
    });


    // --- Initial Load ---
    async function initializePage() {
        await viewModel.fetchStudents();
        renderStudentTable();
        // updateUIStates() is called within renderStudentTable and fetchStudents
    }

    initializePage();
});
