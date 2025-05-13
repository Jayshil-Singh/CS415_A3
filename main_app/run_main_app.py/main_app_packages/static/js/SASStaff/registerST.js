document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessageContainer = document.getElementById('error-message-container');
    const errorTextElement = document.getElementById('error-text');
    const formContainer = document.getElementById('registration-form-container');
    const form = document.getElementById('student-registration-form');

    // Form fields
    const firstNameInput = document.getElementById('first-name');
    const middleNameInput = document.getElementById('middle-name');
    const lastNameInput = document.getElementById('last-name');
    const addressInput = document.getElementById('address');
    const contactInput = document.getElementById('contact');
    const dobInput = document.getElementById('date-of-birth');
    const genderInput = document.getElementById('gender');
    const citizenshipInput = document.getElementById('citizenship');
    const studentLevelInput = document.getElementById('student-level');
    const programSelect = document.getElementById('program');
    const subprogramSelect = document.getElementById('subprogram');
    const campusSelect = document.getElementById('campus');

    const registerButton = document.getElementById('register-button');
    const clearButton = document.getElementById('clear-button');

    // Modal elements for success/error messages
    const messageModal = document.getElementById('message-modal');
    const modalText = document.getElementById('modal-text');
    const closeButton = document.querySelector('#message-modal .close-button'); // More specific selector

    // --- NEW: Registration Confirmation Dialog Elements ---
    const registrationConfirmationDialog = document.getElementById('registration-confirmation-dialog');
    const registrationDialogMessage = document.getElementById('registration-dialog-message'); // If you want to customize its text
    const cancelRegistrationButton = document.getElementById('cancel-registration-button');
    const confirmRegistrationButton = document.getElementById('confirm-registration-button');
    let currentFormDataForSubmission = null; // To store form data temporarily

    // --- ViewModel Simulation ---
    const viewModel = {
        programs: [],
        subprograms: {}, // Store as { programId: [subprograms] } or fetch dynamically
        campuses: [],
        selectedProgram: null,
        selectedSubprogram: null,
        selectedCampus: null,

        loadPrograms: function() {
            return new Promise((resolve) => {
                setTimeout(() => {
                    this.programs = ["Bachelor of Science in IT", "Bachelor of Arts", "Diploma in Business"];
                    this.subprograms["Bachelor of Science in IT"] = ["Software Engineering", "Networking", "Cybersecurity"];
                    this.subprograms["Bachelor of Arts"] = ["History", "Literature"];
                    this.subprograms["Diploma in Business"] = ["Management", "Marketing"];
                    resolve();
                }, 1000);
            });
        },

        loadCampuses: function() {
            return new Promise((resolve) => {
                setTimeout(() => {
                    this.campuses = ["Main Campus (Suva)", "Lautoka Campus", "Labasa Campus"];
                    resolve();
                }, 800);
            });
        },

        submitForm: function(formData) {
            return new Promise((resolve, reject) => {
                console.log("Submitting form data:", formData);
                // This is where you would make an actual API call to your Flask backend
                // For example:
                // fetch('/api/register-student', {
                //     method: 'POST',
                //     headers: { 'Content-Type': 'application/json' },
                //     body: JSON.stringify(formData)
                // })
                // .then(response => response.json())
                // .then(data => {
                //     if (data.success) resolve(data.message || "Student registered successfully!");
                //     else reject(data.error || "Failed to register student.");
                // })
                // .catch(error => reject("Network error or server issue."));

                setTimeout(() => { // Simulating API call
                    const isSuccess = Math.random() > 0.2; // 80% success rate
                    if (isSuccess) {
                        resolve("Student registered successfully!");
                    } else {
                        reject("Failed to register student. Please try again.");
                    }
                }, 1500);
            });
        }
    };

    // --- Helper Functions ---
    function populateSelect(selectElement, options, defaultOptionText = "Select an option") {
        if (!selectElement) return;
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            selectElement.appendChild(optionElement);
        });
    }

    function showLoading() {
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (formContainer) formContainer.style.display = 'none';
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
    }

    function showError(message) {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'none';
        if (errorTextElement) errorTextElement.textContent = `Error loading data: ${message}`;
        if (errorMessageContainer) errorMessageContainer.style.display = 'block';
    }

    function showForm() {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'block';
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
    }

    function showMessageModal(message, isSuccess = true) {
        if (!messageModal || !modalText) return;
        modalText.textContent = message;
        messageModal.className = isSuccess ? 'modal success-modal' : 'modal error-modal'; // Differentiate success/error
        messageModal.style.display = 'flex';
    }

    function hideMessageModal() {
        if (messageModal) messageModal.style.display = 'none';
    }

    // --- NEW: Registration Confirmation Dialog Functions ---
    function showRegistrationConfirmationDialog(formData) {
        if (!registrationConfirmationDialog) return;
        currentFormDataForSubmission = formData; // Store data for when user confirms
        // You can customize the message if needed:
        // registrationDialogMessage.textContent = `Confirm registration for ${formData.firstName} ${formData.lastName}?`;
        registrationConfirmationDialog.style.display = 'flex';
    }

    function hideRegistrationConfirmationDialog() {
        if (registrationConfirmationDialog) registrationConfirmationDialog.style.display = 'none';
        currentFormDataForSubmission = null; // Clear stored form data
    }

    // --- Form Validation ---
    function validateField(inputElement) {
        if (!inputElement) return true; // Should not happen if called correctly
        const errorElement = inputElement.closest('.form-group')?.querySelector('.validation-error'); // More robust selector
        let isValid = true;
        let errorMessage = "";

        if (inputElement.required && (inputElement.value === null || inputElement.value.trim() === '')) {
            isValid = false;
            errorMessage = "This field is required.";
        }

        if (isValid && inputElement.id === 'contact') {
            const regex = /^679-\d{7}$/;
            if (!regex.test(inputElement.value)) {
                isValid = false;
                errorMessage = "Invalid contact format. Expected: 679-XXXXXXX";
            }
        }
        
        if (isValid && inputElement.type === 'date' && inputElement.value) {
            const selectedDate = new Date(inputElement.value);
            const today = new Date();
            today.setHours(0,0,0,0);
            if (selectedDate > today) {
                isValid = false;
                errorMessage = "Date of birth cannot be in the future.";
            }
        }

        if (errorElement) {
            errorElement.textContent = errorMessage;
        }
        inputElement.classList.toggle('invalid', !isValid);
        return isValid;
    }

    function validateForm() {
        let isFormValid = true;
        const inputsToValidate = form.querySelectorAll('input[required], select[required]');
        inputsToValidate.forEach(input => {
            if (!validateField(input)) {
                isFormValid = false;
            }
        });
        if (contactInput && contactInput.value.trim() && !validateField(contactInput)) isFormValid = false;
        return isFormValid;
    }

    // --- Actual Form Submission Logic (called after confirmation) ---
    async function processFormSubmission(formData) {
        registerButton.disabled = true;
        registerButton.textContent = 'Registering...';
        try {
            const successMessage = await viewModel.submitForm(formData);
            showMessageModal(successMessage, true);
            form.reset();
            populateSelect(programSelect, viewModel.programs, "Select program");
            populateSelect(subprogramSelect, [], "Select program first...");
            if (subprogramSelect) subprogramSelect.disabled = true;
            populateSelect(campusSelect, viewModel.campuses, "Select campus");
            form.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        } catch (error) {
            showMessageModal(String(error), false); // Ensure error is a string
        } finally { // Use finally to re-enable button regardless of success/failure
            registerButton.disabled = false;
            registerButton.textContent = 'Register';
        }
    }


    // --- Event Listeners ---
    if (programSelect) {
        programSelect.addEventListener('change', () => {
            viewModel.selectedProgram = programSelect.value;
            const relatedSubprograms = viewModel.subprograms[viewModel.selectedProgram] || [];
            populateSelect(subprogramSelect, relatedSubprograms, "Select subprogram...");
            if (subprogramSelect) subprogramSelect.disabled = relatedSubprograms.length === 0;
            validateField(programSelect);
        });
    }

    if (subprogramSelect) {
        subprogramSelect.addEventListener('change', () => {
            viewModel.selectedSubprogram = subprogramSelect.value;
            validateField(subprogramSelect);
        });
    }
    if (campusSelect) {
        campusSelect.addEventListener('change', () => {
            viewModel.selectedCampus = campusSelect.value;
            validateField(campusSelect);
        });
    }

    if (form) {
        form.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            if (input.tagName.toLowerCase() === 'select') {
                input.addEventListener('change', () => validateField(input));
            } else {
                input.addEventListener('input', () => {
                    if(input.classList.contains('invalid')) {
                        input.classList.remove('invalid');
                        const errorElement = input.closest('.form-group')?.querySelector('.validation-error');
                        if (errorElement) errorElement.textContent = "";
                    }
                });
            }
        });

        form.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            if (validateForm()) {
                const formData = {
                    firstName: firstNameInput?.value,
                    middleName: middleNameInput?.value,
                    lastName: lastNameInput?.value,
                    address: addressInput?.value,
                    contact: contactInput?.value,
                    dateOfBirth: dobInput?.value,
                    gender: genderInput?.value,
                    citizenship: citizenshipInput?.value,
                    studentLevel: studentLevelInput?.value,
                    program: programSelect?.value,
                    subprogram: subprogramSelect?.value,
                    campus: campusSelect?.value,
                };
                // --- MODIFIED: Show confirmation dialog instead of direct submission ---
                showRegistrationConfirmationDialog(formData);
            } else {
                showMessageModal("Please correct the errors in the form.", false);
            }
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (form) form.reset();
            populateSelect(programSelect, viewModel.programs, "Select program");
            populateSelect(subprogramSelect, [], "Select program first...");
            if (subprogramSelect) subprogramSelect.disabled = true;
            populateSelect(campusSelect, viewModel.campuses, "Select campus");
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
            if (firstNameInput) firstNameInput.focus();
        });
    }

    if (closeButton) { // For the success/error message modal
        closeButton.addEventListener('click', hideMessageModal);
    }
    if (messageModal) {
        messageModal.addEventListener('click', (event) => {
            if (event.target === messageModal) {
                hideMessageModal();
            }
        });
    }

    // --- NEW: Event Listeners for Registration Confirmation Dialog ---
    if (cancelRegistrationButton) {
        cancelRegistrationButton.addEventListener('click', () => {
            hideRegistrationConfirmationDialog();
            // Re-enable register button if it was disabled
            if (registerButton) {
                registerButton.disabled = false;
                registerButton.textContent = 'Register';
            }
        });
    }

    if (confirmRegistrationButton) {
        confirmRegistrationButton.addEventListener('click', () => {
            hideRegistrationConfirmationDialog();
            if (currentFormDataForSubmission) {
                processFormSubmission(currentFormDataForSubmission); // Process the stored form data
            }
        });
    }
    
    if (registrationConfirmationDialog) {
        registrationConfirmationDialog.addEventListener('click', (event) => {
            if (event.target === registrationConfirmationDialog) {
                hideRegistrationConfirmationDialog();
                if (registerButton) {
                     registerButton.disabled = false;
                     registerButton.textContent = 'Register';
                }
            }
        });
    }


    // --- Initial Load ---
    async function initializePage() {
        showLoading();
        try {
            await Promise.all([
                viewModel.loadPrograms(),
                viewModel.loadCampuses()
            ]);
            populateSelect(programSelect, viewModel.programs, "Select program");
            populateSelect(campusSelect, viewModel.campuses, "Select campus");
            if (subprogramSelect) subprogramSelect.disabled = true;
            showForm();
        } catch (error) {
            console.error("Initialization error:", error);
            showError(error.message || "Unknown error occurred.");
        }
    }

    if (formContainer) { // Only initialize if the main form container exists
        initializePage();
    } else {
        console.warn("Registration form container not found. Page initialization skipped.");
    }
});
