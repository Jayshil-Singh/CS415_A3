// static/js/SASStaff/registerST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("registerST.js: DOMContentLoaded");

    // DOM Elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessageContainer = document.getElementById('error-message-container');
    const errorTextElement = document.getElementById('error-text');
    const formContainer = document.getElementById('registration-form-container');
    const form = document.getElementById('student-registration-form'); // ID from your HTML

    // Form fields (as in your provided JS)
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

    const registerButton = document.getElementById('register-button'); // Your submit button
    const clearButton = document.getElementById('clear-button');

    // Modals
    const messageModal = document.getElementById('message-modal'); // Your generic message modal
    const modalTextElement = document.getElementById('modal-text-content');
    const closeMessageModalButton = messageModal ? messageModal.querySelector('.close-button') : null;

    const registrationConfirmationDialog = document.getElementById('registration-confirmation-dialog'); // Your existing confirmation dialog
    const cancelRegistrationButton = document.getElementById('cancel-registration-button');
    const confirmRegistrationButton = document.getElementById('confirm-registration-button');

    // NEW: Success Credentials Modal elements (IDs from HTML provided in previous answer)
    const registrationSuccessCredentialsModal = document.getElementById('registration-success-credentials-modal');
    const successStudentIdSpan = document.getElementById('success-student-id');
    const successStudentEmailSpan = document.getElementById('success-student-email');
    const successStudentPasswordSpan = document.getElementById('success-student-password');
    const closeSuccessCredentialsDialogBtn = document.getElementById('close-success-credentials-dialog-btn');

    // Data Store for dropdowns
    let programsData = [];
    let allSubprogrammesData = [];
    let campusesData = [];

    // Store all programs for filtering
    let allProgramsData = [];

    // Function to filter programs based on student level
    function filterProgramsByLevel(level) {
        if (!level) return allProgramsData;

        const levelLower = level.toLowerCase().trim();
        let filteredPrograms = [];

        if (levelLower.includes('certificate')) {
            filteredPrograms = allProgramsData.filter(program => 
                program.toLowerCase().startsWith('certificate'));
        } else if (levelLower.includes('diploma')) {
            filteredPrograms = allProgramsData.filter(program => 
                program.toLowerCase().startsWith('diploma'));
        } else if (levelLower.includes('bachelor') || levelLower.includes('degree')) {
            filteredPrograms = allProgramsData.filter(program => 
                program.toLowerCase().startsWith('bachelor'));
        } else if (levelLower.includes('postgraduate')) {
            filteredPrograms = allProgramsData.filter(program => 
                program.toLowerCase().startsWith('postgraduate'));
        } else if (levelLower.includes('master')) {
            filteredPrograms = allProgramsData.filter(program => 
                program.toLowerCase().startsWith('master'));
        } else {
            return allProgramsData;
        }

        return filteredPrograms;
    }

    // Function to update program dropdown based on student level
    function updateProgramDropdown() {
        const level = studentLevelInput ? studentLevelInput.value : '';
        const filteredPrograms = filterProgramsByLevel(level);
        populateSelect(programSelect, filteredPrograms, "Select Program");
        
        // Reset program type if program is changed
        if (programTypeSelect) {
            programTypeSelect.value = '';
            updateSubprogramUI();
        }
    }

    // Add input event listener to student level input for real-time filtering
    if (studentLevelInput) {
        studentLevelInput.addEventListener('input', updateProgramDropdown);
    }

    // --- UI State Functions ---
    function showLoadingState() {
        if (loadingIndicator) loadingIndicator.style.display = 'block'; // Or 'flex'
        if (formContainer) formContainer.style.display = 'none';
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
        console.log("JS: Showing loading indicator.");
    }

    function showErrorState(message) {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'none';
        if (errorTextElement) errorTextElement.textContent = `Error: ${message}`;
        if (errorMessageContainer) errorMessageContainer.style.display = 'block';
        console.error("JS Error Displayed:", message);
    }

    function showFormState() {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (formContainer) formContainer.style.display = 'block'; // Or 'flex'
        if (errorMessageContainer) errorMessageContainer.style.display = 'none';
        console.log("JS: Showing registration form.");
    }

    // --- Modal Management with Transitions ---
    function showModal(modalElement) {
        if (!modalElement) {
            console.warn(`JS WARN: Attempted to show a non-existent modal.`);
            return;
        }
        modalElement.style.display = 'flex'; // Assuming flex for centering
        setTimeout(() => modalElement.classList.add('active'), 10);
    }

    function hideModal(modalElement) {
        if (!modalElement) {
            console.warn(`JS WARN: Attempted to hide a non-existent modal.`);
            return;
        }
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) {
                modalElement.style.display = 'none';
            }
        }, 300); // Match CSS transition duration
    }

    // Specific Modal Functions
    function showGeneralMessageModal(message, isSuccess = true) {
        if (!messageModal || !modalTextElement) {
            console.error("JS ERROR: Generic message modal or text element not found. Using alert fallback.");
            alert(message);
            return;
        }
        modalTextElement.textContent = message;
        messageModal.classList.remove('success-modal', 'error-modal'); // Assuming you have these classes for styling
        messageModal.classList.add(isSuccess ? 'success-modal' : 'error-modal');
        showModal(messageModal);
    }
    // function hideGeneralMessageModal() { hideModal(messageModal); } // If needed separately


    // --- Populate Select Options ---
    function populateSelect(selectElement, options, defaultOptionText = "Select an option") {
        if (!selectElement) {
            // console.warn(`JS WARN: Select element for "${defaultOptionText}" not found.`);
            return;
        }
        const currentValue = selectElement.value;
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
        if (Array.isArray(options)) {
            options.forEach(option => {
                const optionElement = document.createElement('option');
                const optionValue = (typeof option === 'object' && option !== null && option.value) ? option.value : option;
                const optionText = (typeof option === 'object' && option !== null && option.text) ? option.text : option;
                
                const trimmedOptionValue = String(optionValue).trim();
                optionElement.value = trimmedOptionValue;
                optionElement.textContent = String(optionText).trim();

                if (trimmedOptionValue === currentValue) {
                    optionElement.selected = true;
                }
                selectElement.appendChild(optionElement);
            });
        } else {
            // console.warn(`JS WARN: Options for "${defaultOptionText}" is not an array:`, options);
        }
    }


    // --- Form Logic (Subprogram UI, Validation) ---
    function updateSubprogramUI() {
        const selectedProgramValue = programSelect ? programSelect.value : "";
        let currentProgramType = programTypeSelect ? programTypeSelect.value : "";

        if (programSelect && programTypeSelect) {
            const selectedProgramText = programSelect.options[programSelect.selectedIndex]?.text.toLowerCase() || "";
            if (selectedProgramText.startsWith("certificate") || selectedProgramText.startsWith("diploma")) {
                programTypeSelect.value = "Prescribed Program";
                // Remove disabled state - allow changes but default to Prescribed Program
                programTypeSelect.disabled = false;
                currentProgramType = programTypeSelect.value;
            } else {
                programTypeSelect.disabled = false;
            }
        }

        const showSubprogram1 = currentProgramType === "Single Major" || currentProgramType === "Double Major";
        const showSubprogram2 = currentProgramType === "Double Major";

        [subprogram1Group, subprogram2Group].forEach(group => { if(group) group.style.display = 'none';});
        [subprogram1Select, subprogram2Select].forEach(select => { if(select) select.required = false;});
        [subprogram1RequiredAsterisk, subprogram2RequiredAsterisk].forEach(asterisk => { if(asterisk) asterisk.style.display = 'none';});

        if (subprogram1Group && showSubprogram1) {
            subprogram1Group.style.display = 'block';
            if (subprogram1Select) subprogram1Select.required = true;
            if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = 'inline';
        } else if (subprogram1Select) {
            subprogram1Select.value = ""; 
            validateField(subprogram1Select, false);
        }

        if (subprogram2Group && showSubprogram2) {
            subprogram2Group.style.display = 'block';
            if (subprogram2Select) subprogram2Select.required = true;
            if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = 'inline';
        } else if (subprogram2Select) {
            subprogram2Select.value = "";
            validateField(subprogram2Select, false);
        }
    }

    function validateField(inputElement, showErrorMsg = true) {
        if (!inputElement) return true;
        const group = inputElement.closest('.form-group');
        const errorElement = group?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";

        const isEffectivelyRequired = inputElement.required &&
            (!group || window.getComputedStyle(group).display !== 'none');

        if (isEffectivelyRequired && String(inputElement.value).trim() === '') {
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
            const minBirthYear = new Date().getFullYear() - 100; // e.g., no one older than 100
            const maxBirthYear = new Date().getFullYear() - 15;  // e.g., at least 15 years old
            const minDate = new Date(minBirthYear, 0, 1);
            const maxDate = new Date(maxBirthYear, 11, 31);

            if (selectedDate > maxDate) {
                isValid = false;
                errorMessage = "Student must be at least 15 years old.";
            } else if (selectedDate < minDate) {
                 isValid = false;
                errorMessage = "Date of birth is too far in the past.";
            }
        }

        if (errorElement) {
             errorElement.textContent = showErrorMsg ? errorMessage : "";
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
        if (contactInput && contactInput.value.trim() !== '' && !validateField(contactInput)) {
            isFormValid = false;
        }
        console.log("JS: Form validation result:", isFormValid);
        return isFormValid;
    }

    // --- Event Listeners ---
    if (programSelect) programSelect.addEventListener('change', updateSubprogramUI);
    if (programTypeSelect) programTypeSelect.addEventListener('change', updateSubprogramUI);

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
            event.preventDefault(); // Prevent default HTML submission
            console.log("JS: Form submit event intercepted.");
            updateSubprogramUI(); // Ensure subprogram visibility/required status is current

            if (validateForm()) {
                console.log("JS: Form is valid. Showing confirmation dialog.");
                // No need to collect formData here if we are doing a native submit later
                showModal(registrationConfirmationDialog);
            } else {
                console.warn("JS: Form validation failed on submit.");
                showGeneralMessageModal("Please correct the errors highlighted in the form.", false);
            }
        });
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (form) {
                form.reset();
                // Reset program type enabled state if it was disabled
                if (programTypeSelect) programTypeSelect.disabled = false;
                updateSubprogramUI(); // This will hide subprograms based on reset values
                form.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
                form.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
                if (firstNameInput) firstNameInput.focus();
                console.log("JS: Form cleared.");
            }
        });
    }

    // Registration Confirmation Dialog Listeners
    if (cancelRegistrationButton) {
        cancelRegistrationButton.addEventListener('click', () => {
            hideModal(registrationConfirmationDialog);
            console.log("JS: Registration cancelled by user.");
        });
    }
    if (confirmRegistrationButton) {
        confirmRegistrationButton.addEventListener('click', () => {
            hideModal(registrationConfirmationDialog);
            if (form) {
                console.log("JS: Registration confirmed by user. Submitting form to backend...");
                // Disable button to prevent multiple submissions if desired,
                // but page will navigate away on submit anyway.
                if(registerButton) {
                    registerButton.disabled = true;
                    registerButton.textContent = 'Registering...';
                }
                form.submit(); // Perform actual HTML form submission to Flask
            } else {
                console.error("JS ERROR: Form element not found for submission.");
            }
        });
    }
    if (registrationConfirmationDialog) { // Close on backdrop click
        registrationConfirmationDialog.addEventListener('click', (event) => {
            if (event.target === registrationConfirmationDialog) hideModal(registrationConfirmationDialog);
        });
    }

    // Generic Message Modal Listeners
    if (closeMessageModalButton) { closeMessageModalButton.addEventListener('click', () => hideModal(messageModal)); }
    if (messageModal) { messageModal.addEventListener('click', (event) => { if (event.target === messageModal) hideModal(messageModal); }); }


    // Success Credentials Modal Listeners
    if (closeSuccessCredentialsDialogBtn) {
        closeSuccessCredentialsDialogBtn.addEventListener('click', () => {
            hideModal(registrationSuccessCredentialsModal);
        });
    }
    if (registrationSuccessCredentialsModal) { // Close on backdrop click
        registrationSuccessCredentialsModal.addEventListener('click', (event) => {
            if (event.target === registrationSuccessCredentialsModal) hideModal(registrationSuccessCredentialsModal);
        });
    }

    // --- Initial Page Load ---
    function initializePage() {
        console.log("JS: Initializing page...");
        showLoadingState();
        const initialDataScript = document.getElementById('registration-initial-data');
        if (initialDataScript && initialDataScript.textContent) {
            try {
                const initialData = JSON.parse(initialDataScript.textContent);
                console.log("JS: Initial data from Flask for dropdowns:", initialData);
                allProgramsData = initialData.programs || []; // Store all programs
                programsData = allProgramsData; // Keep the original reference
                allSubprogrammesData = initialData.all_subprogrammes || [];
                campusesData = initialData.campuses || [];

                // Initial population of dropdowns
                updateProgramDropdown(); // This will filter based on current student level
                populateSelect(campusSelect, campusesData, "Select Campus");
                populateSelect(subprogram1Select, allSubprogrammesData, "Select Subprogram 1");
                populateSelect(subprogram2Select, allSubprogrammesData, "Select Subprogram 2");
                
                updateSubprogramUI();
                showFormState();
                console.log("JS: Form initialized and dropdowns populated.");
            } catch (error) {
                console.error("JS ERROR: Parsing initial dropdown data:", error);
                showErrorState("Could not load form options. Please refresh.");
            }
        } else {
            console.error("JS ERROR: Initial registration data script tag not found or empty.");
            showErrorState("Critical form data missing. Please refresh or contact support.");
        }

        // Check for and display new student credentials if passed from backend
        const credentialsDataScript = document.getElementById('new-student-credentials-data');
        if (credentialsDataScript && credentialsDataScript.textContent) {
            try {
                const newStudentCredentials = JSON.parse(credentialsDataScript.textContent);
                if (newStudentCredentials && registrationSuccessCredentialsModal) {
                    console.log("JS: New student credentials found:", newStudentCredentials);
                    if (successStudentIdSpan) successStudentIdSpan.textContent = newStudentCredentials.student_id || 'N/A';
                    if (successStudentEmailSpan) successStudentEmailSpan.textContent = newStudentCredentials.email || 'N/A';
                    if (successStudentPasswordSpan) successStudentPasswordSpan.textContent = newStudentCredentials.password || 'N/A';
                    showModal(registrationSuccessCredentialsModal);
                }
            } catch (error) {
                console.error("JS ERROR: Parsing new student credentials data:", error);
            }
        }
    }

    if (formContainer && loadingIndicator && errorMessageContainer) {
        initializePage();
    } else {
        console.error("JS FATAL: Essential page containers not found. Cannot initialize.");
        if (document.body) document.body.innerHTML = "<p style='color:red; text-align:center; margin-top: 50px;'>Critical page error. Please contact support.</p>";
    }
});