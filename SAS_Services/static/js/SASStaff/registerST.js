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
    const genderSelect = document.getElementById('gender'); // Changed from genderInput
    const citizenshipInput = document.getElementById('citizenship');
    const studentLevelInput = document.getElementById('student-level');
    const programSelect = document.getElementById('program');
    const programTypeSelect = document.getElementById('program-type');
    const subprogram1Select = document.getElementById('subprogram1');
    const subprogram2Select = document.getElementById('subprogram2');
    const subprogram1Group = document.getElementById('subprogram1-group');
    const subprogram2Group = document.getElementById('subprogram2-group');
    const subprogram1RequiredAsterisk = document.getElementById('subprogram1-required-asterisk');
    const subprogram2RequiredAsterisk = document.getElementById('subprogram2-required-asterisk');
    const campusSelect = document.getElementById('campus');

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
        // selectedProgram, selectedProgramType, etc. will be read directly from DOM elements when needed
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

    function populateSelect(selectElement, options, defaultOptionText = "Select an option") {
        if (!selectElement) return;
        const currentValue = selectElement.value; // Preserve current value if possible
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (Array.isArray(options)) {
            options.forEach(option => {
                const optionElement = document.createElement('option');
                const trimmedOption = String(option).trim();
                optionElement.value = trimmedOption;
                optionElement.textContent = trimmedOption;
                if (trimmedOption === currentValue) {
                    optionElement.selected = true;
                }
                selectElement.appendChild(optionElement);
            });
        }
    }

    function showLoading() { if (loadingIndicator) loadingIndicator.style.display = 'block'; if (formContainer) formContainer.style.display = 'none'; if (errorMessageContainer) errorMessageContainer.style.display = 'none'; }
    function showError(message) { if (loadingIndicator) loadingIndicator.style.display = 'none'; if (formContainer) formContainer.style.display = 'none'; if (errorTextElement) errorTextElement.textContent = `Error: ${message}`; if (errorMessageContainer) errorMessageContainer.style.display = 'block'; }
    function showForm() { if (loadingIndicator) loadingIndicator.style.display = 'none'; if (formContainer) formContainer.style.display = 'block'; if (errorMessageContainer) errorMessageContainer.style.display = 'none'; }
    function showMessageModal(message, isSuccess = true) { if (!messageModal || !modalText) return; modalText.textContent = message; messageModal.className = isSuccess ? 'modal success-modal' : 'modal error-modal'; messageModal.style.display = 'flex'; }
    function hideMessageModal() { if (messageModal) messageModal.style.display = 'none'; }
    function showRegistrationConfirmationDialog(formData) { if (!registrationConfirmationDialog) return; currentFormDataForSubmission = formData; registrationConfirmationDialog.style.display = 'flex'; }
    function hideRegistrationConfirmationDialog() { if (registrationConfirmationDialog) registrationConfirmationDialog.style.display = 'none'; currentFormDataForSubmission = null; }

    function updateSubprogramUI() {
        const selectedProgramValue = programSelect ? programSelect.value : "";
        let currentProgramType = programTypeSelect ? programTypeSelect.value : "";

        // Rule: All certificates and diplomas are single majors by default.
        if (selectedProgramValue.toLowerCase().includes("certificate") || selectedProgramValue.toLowerCase().includes("diploma")) {
            if (programTypeSelect) {
                programTypeSelect.value = "Single Major";
                programTypeSelect.disabled = true;
            }
            currentProgramType = "Single Major"; // Override for logic
        } else {
            if (programTypeSelect) {
                programTypeSelect.disabled = false;
            }
        }

        // Subprogram 1 visibility and requirement
        if (currentProgramType === "Single Major" || currentProgramType === "Double Major") {
            if (subprogram1Group) subprogram1Group.style.display = 'block'; // Or 'flex' if it's a flex item
            if (subprogram1Select) subprogram1Select.required = true;
            if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = 'inline';
        } else {
            if (subprogram1Group) subprogram1Group.style.display = 'none';
            if (subprogram1Select) {
                subprogram1Select.required = false;
                subprogram1Select.value = ""; // Clear value if hidden
                validateField(subprogram1Select); // Clear any previous validation error
            }
            if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = 'none';
        }

        // Subprogram 2 visibility and requirement
        if (currentProgramType === "Double Major") {
            if (subprogram2Group) subprogram2Group.style.display = 'block'; // Or 'flex'
            if (subprogram2Select) subprogram2Select.required = true;
            if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = 'inline';
        } else {
            if (subprogram2Group) subprogram2Group.style.display = 'none';
            if (subprogram2Select) {
                subprogram2Select.required = false;
                subprogram2Select.value = ""; // Clear value if hidden
                validateField(subprogram2Select); // Clear any previous validation error
            }
            if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = 'none';
        }
    }

    function validateField(inputElement) {
        if (!inputElement) return true;
        const group = inputElement.closest('.form-group');
        const errorElement = group?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";
        const isVisible = group ? window.getComputedStyle(group).display !== 'none' : true;

        if (inputElement.required && isVisible && String(inputElement.value).trim() === '') {
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
        form.querySelectorAll('input, select').forEach(input => {
            const group = input.closest('.form-group');
            const isVisible = group ? window.getComputedStyle(group).display !== 'none' : true;
            
            if (input.required && isVisible) { // Only validate if required AND visible
                if (!validateField(input)) {
                    isFormValid = false;
                }
            } else if (!input.required && input.classList.contains('invalid') && !isVisible) {
                // Clear errors from hidden, non-required fields
                input.classList.remove('invalid');
                if (group?.querySelector('.validation-error')) {
                    group.querySelector('.validation-error').textContent = "";
                }
            }
        });
        if (contactInput && contactInput.value.trim() && !validateField(contactInput)) isFormValid = false;
        return isFormValid;
    }

    async function processFormSubmission(formData) {
        if(registerButton) { registerButton.disabled = true; registerButton.textContent = 'Registering...'; }
        try {
            const successMessage = await viewModel.submitForm(formData);
            showMessageModal(successMessage, true);
            if (form) form.reset(); // This will trigger change events on selects
            updateSubprogramUI(); // Ensure UI is reset correctly
            
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        } catch (error) {
            showMessageModal(String(error), false);
        } finally {
            if(registerButton){ registerButton.disabled = false; registerButton.textContent = 'Register';}
        }
    }

    // Event Listeners
    if (programSelect) {
        programSelect.addEventListener('change', () => {
            updateSubprogramUI();
            validateField(programSelect); // Validate program itself
            if (programTypeSelect && programTypeSelect.disabled === false) { // If program type wasn't auto-set
                validateField(programTypeSelect); // Re-validate program type
            }
        });
    }

    if (programTypeSelect) {
        programTypeSelect.addEventListener('change', () => {
            updateSubprogramUI();
            validateField(programTypeSelect); // Validate program type itself
        });
    }
    
    [subprogram1Select, subprogram2Select, campusSelect, genderSelect, citizenshipInput, studentLevelInput, addressInput, contactInput, dobInput, firstNameInput, middleNameInput, lastNameInput].forEach(el => {
        if (el) {
            const eventType = el.tagName === 'SELECT' ? 'change' : 'blur';
            el.addEventListener(eventType, () => validateField(el));
             if (el.tagName !== 'SELECT') {
                el.addEventListener('input', () => { // Clear errors on input for text fields
                    if(el.classList.contains('invalid')) {
                        el.classList.remove('invalid');
                        const errorElement = el.closest('.form-group')?.querySelector('.validation-error');
                        if (errorElement) errorElement.textContent = "";
                    }
                });
            }
        }
    });

    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault(); 
            updateSubprogramUI(); // Ensure UI state is correct before validation

            if (validateForm()) {
                const formData = {
                    firstName: firstNameInput?.value,
                    middleName: middleNameInput?.value,
                    lastName: lastNameInput?.value,
                    address: addressInput?.value,
                    contact: contactInput?.value,
                    dateOfBirth: dobInput?.value,
                    gender: genderSelect?.value,
                    citizenship: citizenshipInput?.value,
                    studentLevel: studentLevelInput?.value,
                    program: programSelect?.value,
                    programType: programTypeSelect?.value,
                    subprogram1: (subprogram1Group?.style.display !== 'none' && subprogram1Select) ? subprogram1Select.value : "",
                    subprogram2: (subprogram2Group?.style.display !== 'none' && subprogram2Select) ? subprogram2Select.value : "",
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
            if (form) form.reset(); // This should trigger change events on selects
            updateSubprogramUI(); // Call this to reset visibility and required states
            
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
            if (firstNameInput) firstNameInput.focus();
        });
    }

    // Modal event listeners
    if (closeButton) { closeButton.addEventListener('click', hideMessageModal); }
    if (messageModal) { messageModal.addEventListener('click', (event) => { if (event.target === messageModal) hideMessageModal(); }); }
    if (cancelRegistrationButton) { cancelRegistrationButton.addEventListener('click', () => { hideRegistrationConfirmationDialog(); if (registerButton) { registerButton.disabled = false; registerButton.textContent = 'Register';}}); }
    if (confirmRegistrationButton) { confirmRegistrationButton.addEventListener('click', () => { hideRegistrationConfirmationDialog(); if (currentFormDataForSubmission) processFormSubmission(currentFormDataForSubmission); }); }
    if (registrationConfirmationDialog) { registrationConfirmationDialog.addEventListener('click', (event) => { if (event.target === registrationConfirmationDialog) { hideRegistrationConfirmationDialog(); if (registerButton) { registerButton.disabled = false; registerButton.textContent = 'Register';}}});}

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
                // Program Type is static in HTML

                // Populate subprogram dropdowns but let updateSubprogramUI handle visibility/disabled
                populateSelect(subprogram1Select, allSubprogrammesData, "Select subprogram 1");
                populateSelect(subprogram2Select, allSubprogrammesData, "Select subprogram 2");
                
                updateSubprogramUI(); // Set initial state based on default selections
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
