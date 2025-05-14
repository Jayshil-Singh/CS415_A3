document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessageContainer = document.getElementById('error-message-container');
    const errorTextElement = document.getElementById('error-text');
    const formContainer = document.getElementById('registration-form-container');
    const form = document.getElementById('student-registration-form');

    // Form fields
    const firstNameInput = document.getElementById('first-name');
    // ... other existing form field references ...
    const programSelect = document.getElementById('program');
    const programTypeSelect = document.getElementById('program-type'); // New
    const subprogram1Select = document.getElementById('subprogram1'); // Renamed
    const subprogram2Select = document.getElementById('subprogram2'); // New
    const subprogram1Group = document.getElementById('subprogram1-group');
    const subprogram2Group = document.getElementById('subprogram2-group');
    const subprogram1RequiredAsterisk = document.getElementById('subprogram1-required-asterisk');
    const subprogram2RequiredAsterisk = document.getElementById('subprogram2-required-asterisk');
    const campusSelect = document.getElementById('campus');
    // Add other input elements like gender, citizenship, studentLevel here if not already
    const genderInput = document.getElementById('gender');
    const citizenshipInput = document.getElementById('citizenship');
    const studentLevelInput = document.getElementById('student-level');
    const addressInput = document.getElementById('address');
    const contactInput = document.getElementById('contact');
    const dobInput = document.getElementById('date-of-birth');
    const middleNameInput = document.getElementById('middle-name');
    const lastNameInput = document.getElementById('last-name');


    const registerButton = document.getElementById('register-button');
    const clearButton = document.getElementById('clear-button');

    // Modals
    const messageModal = document.getElementById('message-modal');
    const modalText = document.getElementById('modal-text');
    const closeButton = document.querySelector('#message-modal .close-button');
    const registrationConfirmationDialog = document.getElementById('registration-confirmation-dialog');
    const cancelRegistrationButton = document.getElementById('cancel-registration-button');
    const confirmRegistrationButton = document.getElementById('confirm-registration-button');
    let currentFormDataForSubmission = null;

    // Data Store
    let programsData = [];
    let allSubprogrammesData = [];
    let campusesData = [];

    // ViewModel
    const viewModel = {
        selectedProgram: null,
        selectedProgramType: null,
        selectedSubprogram1: null,
        selectedSubprogram2: null,
        selectedCampus: null,
        submitForm: function(formData) {
            return new Promise((resolve, reject) => {
                console.log("Submitting form data to backend:", formData);
                // Simulate API call
                setTimeout(() => {
                    const isSuccess = Math.random() > 0.2;
                    if (isSuccess) {
                        resolve("Student registered successfully! (Simulated)");
                    } else {
                        reject("Failed to register student. Please try again. (Simulated)");
                    }
                }, 1500);
            });
        }
    };

    // Helper Functions
    function populateSelect(selectElement, options, defaultOptionText = "Select an option") {
        if (!selectElement) return;
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (Array.isArray(options)) {
            options.forEach(option => {
                const optionElement = document.createElement('option');
                const trimmedOption = String(option).trim();
                optionElement.value = trimmedOption;
                optionElement.textContent = trimmedOption;
                selectElement.appendChild(optionElement);
            });
        }
    }

    function showLoading() { /* ... */ 
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (formContainer) formContainer.style.display = 'none';
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
    }
    function showError(message) { /* ... */ 
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'none';
        if (errorTextElement) errorTextElement.textContent = `Error: ${message}`;
        if (errorMessageContainer) errorMessageContainer.style.display = 'block';
    }
    function showForm() { /* ... */ 
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'block';
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
    }
    function showMessageModal(message, isSuccess = true) { /* ... */ 
        if (!messageModal || !modalText) return;
        modalText.textContent = message;
        messageModal.className = isSuccess ? 'modal success-modal' : 'modal error-modal';
        messageModal.style.display = 'flex';
    }
    function hideMessageModal() { /* ... */ 
        if (messageModal) messageModal.style.display = 'none';
    }
    function showRegistrationConfirmationDialog(formData) { /* ... */ 
        if (!registrationConfirmationDialog) return;
        currentFormDataForSubmission = formData;
        registrationConfirmationDialog.style.display = 'flex';
    }
    function hideRegistrationConfirmationDialog() { /* ... */ 
        if (registrationConfirmationDialog) registrationConfirmationDialog.style.display = 'none';
        currentFormDataForSubmission = null;
    }
    
    function updateSubprogramVisibilityAndRequirement() {
        const selectedProgramText = programSelect?.value || "";
        const selectedProgramType = programTypeSelect?.value || "";

        // Default to Single Major for Certificates and Diplomas
        if (selectedProgramText.toLowerCase().includes("certificate") || selectedProgramText.toLowerCase().includes("diploma")) {
            if (programTypeSelect) {
                programTypeSelect.value = "Single Major";
                programTypeSelect.disabled = true;
            }
            // Update selectedProgramType for subsequent logic
            viewModel.selectedProgramType = "Single Major";
        } else {
            if (programTypeSelect) {
                programTypeSelect.disabled = false;
            }
            viewModel.selectedProgramType = selectedProgramType; // Use user's selection
        }
        
        // Now use viewModel.selectedProgramType for logic
        const currentType = viewModel.selectedProgramType;

        // Subprogram 1
        if (currentType === "Single Major" || currentType === "Double Major") {
            if (subprogram1Group) subprogram1Group.style.display = 'block';
            if (subprogram1Select) subprogram1Select.required = true;
            if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = 'inline';
            populateSelect(subprogram1Select, allSubprogrammesData, "Select subprogram 1");
        } else {
            if (subprogram1Group) subprogram1Group.style.display = 'none';
            if (subprogram1Select) {
                subprogram1Select.required = false;
                subprogram1Select.value = ""; // Clear value
            }
            if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = 'none';
        }

        // Subprogram 2
        if (currentType === "Double Major") {
            if (subprogram2Group) subprogram2Group.style.display = 'block';
            if (subprogram2Select) subprogram2Select.required = true;
            if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = 'inline';
            populateSelect(subprogram2Select, allSubprogrammesData, "Select subprogram 2");
        } else {
            if (subprogram2Group) subprogram2Group.style.display = 'none';
            if (subprogram2Select) {
                subprogram2Select.required = false;
                subprogram2Select.value = ""; // Clear value
            }
            if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = 'none';
        }
        // Re-validate subprogram fields after changing their state
        if (subprogram1Select) validateField(subprogram1Select);
        if (subprogram2Select) validateField(subprogram2Select);
    }


    function validateField(inputElement) {
        if (!inputElement) return true;
        const errorElement = inputElement.closest('.form-group')?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";

        // Check if the element is visible and required
        const isVisible = inputElement.offsetParent !== null || inputElement.closest('.form-group')?.style.display !== 'none';

        if (inputElement.required && isVisible && (inputElement.value === null || String(inputElement.value).trim() === '')) {
            isValid = false;
            errorMessage = "This field is required.";
        }

        if (isValid && inputElement.id === 'contact' && inputElement.value.trim() !== '') {
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
        // Validate all fields that are currently marked as required and visible
        const inputsToValidate = form.querySelectorAll('input, select'); 
        inputsToValidate.forEach(input => {
            // Only validate if it's required AND its group is visible
            const group = input.closest('.form-group');
            const isVisible = group ? group.style.display !== 'none' : true; // Assume visible if not in a group with display style
            
            if (input.required && isVisible) {
                if (!validateField(input)) {
                    isFormValid = false;
                }
            } else if (!input.required && input.classList.contains('invalid')) {
                // Clear previous errors from fields that are no longer required or hidden
                input.classList.remove('invalid');
                const errorElement = group?.querySelector('.validation-error');
                if (errorElement) errorElement.textContent = "";
            }
        });
        // Special validation for contact even if not marked required but has value
        if (contactInput && contactInput.value.trim() && !validateField(contactInput)) isFormValid = false;
        return isFormValid;
    }

    async function processFormSubmission(formData) {
        if(registerButton) {
            registerButton.disabled = true;
            registerButton.textContent = 'Registering...';
        }
        try {
            const successMessage = await viewModel.submitForm(formData);
            showMessageModal(successMessage, true);
            if (form) form.reset(); // This will trigger change events on selects, resetting them
            // Manually call update to ensure subprogram states are correct after reset
            updateSubprogramVisibilityAndRequirement(); 
            
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        } catch (error) {
            showMessageModal(String(error), false);
        } finally {
            if(registerButton){
                registerButton.disabled = false;
                registerButton.textContent = 'Register';
            }
        }
    }

    // --- Event Listeners ---
    if (programSelect) {
        programSelect.addEventListener('change', () => {
            viewModel.selectedProgram = programSelect.value;
            updateSubprogramVisibilityAndRequirement(); // Centralized logic
            validateField(programSelect);
        });
    }

    if (programTypeSelect) {
        programTypeSelect.addEventListener('change', () => {
            viewModel.selectedProgramType = programTypeSelect.value;
            updateSubprogramVisibilityAndRequirement(); // Centralized logic
            validateField(programTypeSelect);
        });
    }
    
    if (subprogram1Select) {
        subprogram1Select.addEventListener('change', () => {
            viewModel.selectedSubprogram1 = subprogram1Select.value;
            validateField(subprogram1Select);
        });
    }
    if (subprogram2Select) {
        subprogram2Select.addEventListener('change', () => {
            viewModel.selectedSubprogram2 = subprogram2Select.value;
            validateField(subprogram2Select);
        });
    }

    if (campusSelect) { /* ... (same as before) ... */ 
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
            event.preventDefault(); 
            // Ensure subprogram states are correct before validation
            updateSubprogramVisibilityAndRequirement(); 

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
                    programType: programTypeSelect?.value, // New
                    subprogram1: (subprogram1Select && subprogram1Select.closest('.form-group')?.style.display !== 'none') ? subprogram1Select.value : "", // New
                    subprogram2: (subprogram2Select && subprogram2Select.closest('.form-group')?.style.display !== 'none') ? subprogram2Select.value : "", // New
                    campus: campusSelect?.value,
                };
                showRegistrationConfirmationDialog(formData);
            } else {
                showMessageModal("Please correct the errors in the form.", false);
            }
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (form) form.reset(); // This will trigger change events on selects
            // Manually call update to ensure subprogram states are correct after reset
            updateSubprogramVisibilityAndRequirement(); 
            
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
            if (firstNameInput) firstNameInput.focus();
        });
    }

    // Modal event listeners (same as before)
    if (closeButton) { closeButton.addEventListener('click', hideMessageModal); }
    if (messageModal) { messageModal.addEventListener('click', (event) => { if (event.target === messageModal) hideMessageModal(); }); }
    if (cancelRegistrationButton) { 
        cancelRegistrationButton.addEventListener('click', () => {
            hideRegistrationConfirmationDialog();
            if (registerButton) { registerButton.disabled = false; registerButton.textContent = 'Register';}
        }); 
    }
    if (confirmRegistrationButton) { 
        confirmRegistrationButton.addEventListener('click', () => {
            hideRegistrationConfirmationDialog();
            if (currentFormDataForSubmission) processFormSubmission(currentFormDataForSubmission);
        });
    }
    if (registrationConfirmationDialog) { 
        registrationConfirmationDialog.addEventListener('click', (event) => { 
            if (event.target === registrationConfirmationDialog) {
                hideRegistrationConfirmationDialog();
                if (registerButton) { registerButton.disabled = false; registerButton.textContent = 'Register';}
            }
        });
    }

    // Initial Load
    function initializePage() {
        showLoading(); 
        const dataScriptElement = document.getElementById('registration-initial-data');
        if (dataScriptElement) {
            try {
                const initialData = JSON.parse(dataScriptElement.textContent);
                programsData = initialData.programs || [];
                allSubprogrammesData = initialData.all_subprogrammes || [];
                campusesData = initialData.campuses || [];

                populateSelect(programSelect, programsData, "Select program");
                populateSelect(campusSelect, campusesData, "Select campus");
                // Program Type is static, already in HTML
                
                // Initialize subprogram dropdowns but keep them hidden/disabled until type is selected
                populateSelect(subprogram1Select, allSubprogrammesData, "Select subprogram 1");
                populateSelect(subprogram2Select, allSubprogrammesData, "Select subprogram 2");
                updateSubprogramVisibilityAndRequirement(); // Set initial state

                showForm();
            } catch (error) {
                console.error("Error parsing initial registration data from HTML:", error);
                showError("Could not load initial form data. Please refresh the page.");
            }
        } else {
            console.error("Initial registration data script tag not found.");
            showError("Critical data missing. Please contact support.");
        }
    }

    if (formContainer) {
        initializePage();
    } else {
        console.warn("Registration form container not found. Page initialization skipped.");
    }
});
