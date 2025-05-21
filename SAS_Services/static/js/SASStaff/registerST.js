// static/js/SASStaff/registerST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("registerST.js: DOMContentLoaded");

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
    const genderSelect = document.getElementById('gender');
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
    const modalTextElement = document.getElementById('modal-text-content'); // Corrected ID from your HTML
    const closeMessageModalButton = document.querySelector('#message-modal .close-button'); // Corrected selector

    const registrationConfirmationDialog = document.getElementById('registration-confirmation-dialog');
    const cancelRegistrationButton = document.getElementById('cancel-registration-button');
    const confirmRegistrationButton = document.getElementById('confirm-registration-button');
    
    let currentFormDataForSubmission = null; // To hold validated data before final confirmation

    // Data Store
    let programsData = [];
    let allSubprogrammesData = []; // This will hold the flat list of all subprogrammes
    // let subprogramsMapData = {}; // Use this if your backend provides a map
    let campusesData = [];

    // ViewModel
    const viewModel = {
        // Mock API call to simulate form submission
        submitForm: function(formData) {
            return new Promise((resolve, reject) => {
                console.log("JS: Submitting form data to backend (mock):", formData);
                // Simulate API call delay
                setTimeout(() => {
                    const isSuccess = Math.random() > 0.1; // 90% success rate for simulation
                    if (isSuccess) {
                        console.log("JS: Mock submission successful.");
                        resolve(`Student "${formData.firstName} ${formData.lastName}" registered successfully! (Simulated)`);
                    } else {
                        console.warn("JS: Mock submission failed.");
                        reject("Failed to register student. Please try again. (Simulated Error)");
                    }
                }, 1500);
            });
        }
    };

    function populateSelect(selectElement, options, defaultOptionText = "Select an option") {
        if (!selectElement) {
            console.warn(`JS WARN: Select element for "${defaultOptionText}" not found.`);
            return;
        }
        const currentValue = selectElement.value; 
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (Array.isArray(options)) {
            options.forEach(option => {
                const optionElement = document.createElement('option');
                const trimmedOption = String(option).trim(); // Ensure it's a string and trim
                optionElement.value = trimmedOption;
                optionElement.textContent = trimmedOption;
                if (trimmedOption === currentValue) {
                    optionElement.selected = true;
                }
                selectElement.appendChild(optionElement);
            });
        } else {
            console.warn(`JS WARN: Options for "${defaultOptionText}" is not an array:`, options);
        }
    }

    // --- UI State Functions ---
    function showLoading() { 
        if (loadingIndicator) loadingIndicator.style.display = 'block'; 
        if (formContainer) formContainer.style.display = 'none'; 
        if (errorMessageContainer) errorMessageContainer.style.display = 'none'; 
        console.log("JS: Showing loading indicator.");
    }
    function showError(message) { 
        if (loadingIndicator) loadingIndicator.style.display = 'none'; 
        if (formContainer) formContainer.style.display = 'none'; 
        if (errorTextElement) errorTextElement.textContent = `Error: ${message}`; 
        if (errorMessageContainer) errorMessageContainer.style.display = 'block'; 
        console.error("JS Error Displayed:", message);
    }
    function showForm() { 
        if (loadingIndicator) loadingIndicator.style.display = 'none'; 
        if (formContainer) formContainer.style.display = 'block'; // Or 'flex' if it's a flex container
        if (errorMessageContainer) errorMessageContainer.style.display = 'none'; 
        console.log("JS: Showing registration form.");
    }

    // --- Modal Management with Transitions ---
    function showModal(modalElement) {
        if (!modalElement) {
            console.warn(`JS WARN: Attempted to show a non-existent modal.`);
            return;
        }
        modalElement.style.display = 'flex';
        setTimeout(() => modalElement.classList.add('active'), 10); // For CSS transition
    }

    function hideModal(modalElement) {
        if (!modalElement) {
            console.warn(`JS WARN: Attempted to hide a non-existent modal.`);
            return;
        }
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) { // Ensure it wasn't re-opened
                 modalElement.style.display = 'none';
            }
        }, 300); // Match CSS transition duration (e.g., 0.3s)
    }
    
    // Specific Modal Functions
    function showMessageModal(message, isSuccess = true) { 
        if (!messageModal || !modalTextElement) {
            console.error("JS ERROR: Message modal or text element not found. Using alert fallback.");
            alert(message); // Fallback
            return;
        }
        modalTextElement.textContent = message;
        messageModal.classList.remove('success-modal', 'error-modal'); // Clear previous
        messageModal.classList.add(isSuccess ? 'success-modal' : 'error-modal');
        showModal(messageModal);
    }
    function hideMessageModal() { hideModal(messageModal); }

    function showRegistrationConfirmationDialog(formData) { 
        if (!registrationConfirmationDialog) {
            console.error("JS ERROR: Registration confirmation dialog not found.");
            // Fallback: process immediately if dialog is missing (not ideal)
            // processFormSubmission(formData); 
            return;
        }
        currentFormDataForSubmission = formData; // Store data for when user confirms
        // You can customize the message here if needed, e.g., by adding student name
        // const dialogMessageEl = document.getElementById('registration-dialog-message');
        // if (dialogMessageEl) dialogMessageEl.textContent = `Register ${formData.firstName} ${formData.lastName}?`;
        showModal(registrationConfirmationDialog);
    }
    function hideRegistrationConfirmationDialog() { 
        hideModal(registrationConfirmationDialog);
        // currentFormDataForSubmission = null; // Clear only after processing or explicit cancel
    }

    // --- Form Logic ---
    function updateSubprogramUI() {
        const selectedProgramValue = programSelect ? programSelect.value : "";
        let currentProgramType = programTypeSelect ? programTypeSelect.value : "";

        if (programSelect && programTypeSelect) { // Ensure elements exist
            if (selectedProgramValue.toLowerCase().includes("certificate") || selectedProgramValue.toLowerCase().includes("diploma")) {
                programTypeSelect.value = "Single Major";
                programTypeSelect.disabled = true;
                currentProgramType = "Single Major"; 
            } else {
                programTypeSelect.disabled = false;
            }
        }

        const showSubprogram1 = currentProgramType === "Single Major" || currentProgramType === "Double Major";
        const showSubprogram2 = currentProgramType === "Double Major";

        if (subprogram1Group) subprogram1Group.style.display = showSubprogram1 ? 'block' : 'none';
        if (subprogram1Select) subprogram1Select.required = showSubprogram1;
        if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = showSubprogram1 ? 'inline' : 'none';
        if (!showSubprogram1 && subprogram1Select) {
             subprogram1Select.value = ""; 
             validateField(subprogram1Select, false); // Validate to clear error if any
        }

        if (subprogram2Group) subprogram2Group.style.display = showSubprogram2 ? 'block' : 'none';
        if (subprogram2Select) subprogram2Select.required = showSubprogram2;
        if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = showSubprogram2 ? 'inline' : 'none';
        if (!showSubprogram2 && subprogram2Select) {
            subprogram2Select.value = ""; 
            validateField(subprogram2Select, false); // Validate to clear error if any
        }
    }

    function validateField(inputElement, showErrorMsg = true) {
        if (!inputElement) return true;
        const group = inputElement.closest('.form-group');
        const errorElement = group?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";
        
        // Check if the field is visible and required
        const isVisibleAndRequired = inputElement.required && 
                                   group && 
                                   window.getComputedStyle(group).display !== 'none';

        if (isVisibleAndRequired && String(inputElement.value).trim() === '') {
            isValid = false;
            errorMessage = "This field is required.";
        }

        if (isValid && inputElement.id === 'contact' && inputElement.value.trim() !== '') {
            const regex = /^679-\d{7}$/; // Fiji contact format
            if (!regex.test(inputElement.value)) {
                isValid = false;
                errorMessage = "Invalid contact. Expected: 679-XXXXXXX";
            }
        }
        
        if (isValid && inputElement.type === 'date' && inputElement.value) {
            const selectedDate = new Date(inputElement.value);
            const today = new Date();
            today.setHours(0,0,0,0); // Compare dates only
            if (selectedDate > today) {
                isValid = false;
                errorMessage = "Date of birth cannot be in the future.";
            }
        }

        if (errorElement && showErrorMsg) {
            errorElement.textContent = errorMessage;
        } else if (errorElement && !showErrorMsg) {
            errorElement.textContent = ""; // Clear error if not showing
        }
        inputElement.classList.toggle('invalid', !isValid && showErrorMsg);
        return isValid;
    }

    function validateForm() {
        console.log("JS: Validating form...");
        let isFormValid = true;
        if (!form) return false;

        form.querySelectorAll('input[required], select[required]').forEach(input => {
            if (!validateField(input)) {
                isFormValid = false;
            }
        });
        // Validate contact even if not required, if it has a value
        if (contactInput && contactInput.value.trim() !== '' && !validateField(contactInput)) {
            isFormValid = false;
        }
        console.log("JS: Form validation result:", isFormValid);
        return isFormValid;
    }

    async function processFormSubmission(formData) {
        console.log("JS: processFormSubmission called with data:", formData);
        if(registerButton) { 
            registerButton.disabled = true; 
            registerButton.textContent = 'Registering...'; 
        }
        try {
            const successMessage = await viewModel.submitForm(formData);
            showMessageModal(successMessage, true); // Show success message modal
            if (form) form.reset(); 
            updateSubprogramUI(); // Reset subprogram UI
            
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        } catch (error) {
            showMessageModal(String(error), false); // Show error message modal
        } finally {
            if(registerButton){ 
                registerButton.disabled = false; 
                registerButton.textContent = 'Register Student';
            }
            currentFormDataForSubmission = null; // Clear stored data
        }
    }

    // --- Event Listeners ---
    if (programSelect) {
        programSelect.addEventListener('change', () => {
            updateSubprogramUI();
            validateField(programSelect); 
            if (programTypeSelect && !programTypeSelect.disabled) {
                validateField(programTypeSelect); 
            }
        });
    }

    if (programTypeSelect) {
        programTypeSelect.addEventListener('change', () => {
            updateSubprogramUI();
            validateField(programTypeSelect); 
        });
    }
    
    // Add blur/change listeners for individual field validation
    const fieldsToValidateOnBlur = [
        firstNameInput, middleNameInput, lastNameInput, addressInput, contactInput, 
        dobInput, citizenshipInput, studentLevelInput
    ];
    const selectsToValidateOnChange = [
        genderSelect, programSelect, programTypeSelect, subprogram1Select, 
        subprogram2Select, campusSelect
    ];

    fieldsToValidateOnBlur.forEach(el => {
        if (el) el.addEventListener('blur', () => validateField(el));
    });
    selectsToValidateOnChange.forEach(el => {
        if (el) el.addEventListener('change', () => validateField(el));
    });


    if (form) {
        form.addEventListener('submit', (event) => {
            event.preventDefault(); 
            console.log("JS: Form submit event triggered.");
            updateSubprogramUI(); // Ensure UI state is correct before final validation

            if (validateForm()) {
                console.log("JS: Form is valid. Preparing data for confirmation.");
                const formData = {
                    firstName: firstNameInput?.value.trim(),
                    middleName: middleNameInput?.value.trim(),
                    lastName: lastNameInput?.value.trim(),
                    address: addressInput?.value.trim(),
                    contact: contactInput?.value.trim(),
                    dateOfBirth: dobInput?.value,
                    gender: genderSelect?.value,
                    citizenship: citizenshipInput?.value.trim(),
                    studentLevel: studentLevelInput?.value.trim(),
                    program: programSelect?.value,
                    programType: programTypeSelect?.value,
                    subprogram1: (subprogram1Group?.style.display !== 'none' && subprogram1Select) ? subprogram1Select.value : "",
                    subprogram2: (subprogram2Group?.style.display !== 'none' && subprogram2Select) ? subprogram2Select.value : "",
                    campus: campusSelect?.value,
                };
                showRegistrationConfirmationDialog(formData); // MODIFIED: Show confirmation dialog
            } else {
                console.warn("JS: Form validation failed on submit.");
                showMessageModal("Please correct the errors in the form.", false);
            }
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (form) form.reset(); 
            updateSubprogramUI(); 
            form?.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
            form?.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
            if (firstNameInput) firstNameInput.focus();
            console.log("JS: Form cleared.");
        });
    }

    // Modal event listeners
    if (closeMessageModalButton) { closeMessageModalButton.addEventListener('click', hideMessageModal); }
    if (messageModal) { messageModal.addEventListener('click', (event) => { if (event.target === messageModal) hideMessageModal(); }); }
    
    if (cancelRegistrationButton) { 
        cancelRegistrationButton.addEventListener('click', () => {
            hideRegistrationConfirmationDialog(); 
            currentFormDataForSubmission = null; // Clear data if cancelled
            if (registerButton) { 
                registerButton.disabled = false; 
                registerButton.textContent = 'Register Student';
            }
        }); 
    }
    if (confirmRegistrationButton) { 
        confirmRegistrationButton.addEventListener('click', () => { 
            hideRegistrationConfirmationDialog(); 
            if (currentFormDataForSubmission) {
                processFormSubmission(currentFormDataForSubmission); 
            } else {
                console.error("JS ERROR: No form data to submit after confirmation.");
            }
        }); 
    }
    if (registrationConfirmationDialog) { 
        registrationConfirmationDialog.addEventListener('click', (event) => { 
            if (event.target === registrationConfirmationDialog) {
                hideRegistrationConfirmationDialog(); 
                currentFormDataForSubmission = null; // Clear data if overlay is clicked
                if (registerButton) { 
                    registerButton.disabled = false; 
                    registerButton.textContent = 'Register Student';
                }
            }
        });
    }

    // --- Initial Page Load ---
    async function initializePage() {
        console.log("JS: Initializing page...");
        showLoading(); 
        const dataScriptElement = document.getElementById('registration-initial-data');
        if (dataScriptElement && dataScriptElement.textContent) {
            try {
                const initialData = JSON.parse(dataScriptElement.textContent);
                console.log("JS: Initial data from Flask:", initialData);
                programsData = initialData.programs || [];
                allSubprogrammesData = initialData.all_subprogrammes || [];
                // subprogramsMapData = initialData.subprograms_map || {}; // If you use a map
                campusesData = initialData.campuses || [];

                populateSelect(programSelect, programsData, "Select Program");
                populateSelect(campusSelect, campusesData, "Select Campus");
                // Program Type is static in HTML for now

                populateSelect(subprogram1Select, allSubprogrammesData, "Select Subprogram 1");
                populateSelect(subprogram2Select, allSubprogrammesData, "Select Subprogram 2");
                
                updateSubprogramUI(); 
                showForm();
                console.log("JS: Form initialized and shown.");
            } catch (error) {
                console.error("JS ERROR: Error parsing initial registration data from HTML:", error, "Raw content:", dataScriptElement.textContent);
                showError("Could not load initial form data. Please refresh the page.");
            }
        } else {
            console.error("JS ERROR: Initial registration data script tag not found or empty.");
            showError("Critical data missing. Please contact support or refresh.");
        }
    }

    if (formContainer && loadingIndicator && errorMessageContainer) { // Check essential containers
        initializePage();
    } else {
        console.error("JS FATAL: Essential page containers (form, loading, or error) not found. Cannot initialize.");
    }
});