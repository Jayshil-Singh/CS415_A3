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

    // Modal elements
    const messageModal = document.getElementById('message-modal');
    const modalText = document.getElementById('modal-text');
    const closeButton = document.querySelector('.close-button');

    // --- ViewModel Simulation ---
    const viewModel = {
        programs: [],
        subprograms: {}, // Store as { programId: [subprograms] } or fetch dynamically
        campuses: [],
        selectedProgram: null,
        selectedSubprogram: null,
        selectedCampus: null,

        // Simulate loading programs (replace with actual API call)
        loadPrograms: function() {
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    this.programs = ["Bachelor of Science in IT", "Bachelor of Arts", "Diploma in Business"];
                    // Example subprograms for the first program
                    this.subprograms["Bachelor of Science in IT"] = ["Software Engineering", "Networking", "Cybersecurity"];
                    this.subprograms["Bachelor of Arts"] = ["History", "Literature"];
                    this.subprograms["Diploma in Business"] = ["Management", "Marketing"];
                    resolve();
                }, 1000); // Simulate network delay
            });
        },

        // Simulate loading campuses
        loadCampuses: function() {
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    this.campuses = ["Main Campus (Suva)", "Lautoka Campus", "Labasa Campus"];
                    resolve();
                }, 800);
            });
        },

        // Simulate form submission
        submitForm: function(formData) {
            return new Promise((resolve, reject) => {
                console.log("Submitting form data:", formData);
                setTimeout(() => {
                    // Simulate success/failure
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
        selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`; // Clear existing and add default
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            selectElement.appendChild(optionElement);
        });
    }

    function showLoading() {
        loadingIndicator.style.display = 'block';
        formContainer.style.display = 'none';
        errorMessageContainer.style.display = 'none';
    }

    function showError(message) {
        loadingIndicator.style.display = 'none';
        formContainer.style.display = 'none';
        errorTextElement.textContent = `Error loading data: ${message}`;
        errorMessageContainer.style.display = 'block';
    }

    function showForm() {
        loadingIndicator.style.display = 'none';
        formContainer.style.display = 'block';
        errorMessageContainer.style.display = 'none';
    }

    function showModal(message, isSuccess = true) {
        modalText.textContent = message;
        messageModal.className = isSuccess ? 'modal success' : 'modal error-modal'; // Add classes for styling
        messageModal.style.display = 'flex';
    }

    function hideModal() {
        messageModal.style.display = 'none';
    }

    // --- Form Validation ---
    function validateField(inputElement) {
        const errorElement = inputElement.nextElementSibling; // Assuming error span is next sibling
        let isValid = true;
        let errorMessage = "";

        // Required validation
        if (inputElement.required && !inputElement.value.trim()) {
            isValid = false;
            errorMessage = "This field is required.";
        }

        // Specific validations
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
            today.setHours(0,0,0,0); // Compare dates only
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
        // Also validate non-required but format-specific fields like contact if it has a value
        if (contactInput.value.trim() && !validateField(contactInput)) isFormValid = false;

        return isFormValid;
    }

    // --- Event Listeners ---
    programSelect.addEventListener('change', () => {
        viewModel.selectedProgram = programSelect.value;
        const relatedSubprograms = viewModel.subprograms[viewModel.selectedProgram] || [];
        populateSelect(subprogramSelect, relatedSubprograms, "Select subprogram...");
        subprogramSelect.disabled = relatedSubprograms.length === 0;
        validateField(programSelect); // Validate on change
    });

    subprogramSelect.addEventListener('change', () => {
        viewModel.selectedSubprogram = subprogramSelect.value;
        validateField(subprogramSelect);
    });
    campusSelect.addEventListener('change', () => {
        viewModel.selectedCampus = campusSelect.value;
        validateField(campusSelect);
    });

    // Add blur/input event listeners for instant validation feedback
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        // For select, 'change' is often better than 'input'
        if (input.tagName.toLowerCase() === 'select') {
             input.addEventListener('change', () => validateField(input));
        } else {
             input.addEventListener('input', () => {
                // Clear error on input, re-validate on blur
                if(input.classList.contains('invalid')) {
                    input.classList.remove('invalid');
                    const errorElement = input.nextElementSibling;
                    if (errorElement) errorElement.textContent = "";
                }
            });
        }
    });


    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        registerButton.disabled = true;
        registerButton.textContent = 'Registering...';

        if (validateForm()) {
            const formData = {
                firstName: firstNameInput.value,
                middleName: middleNameInput.value,
                lastName: lastNameInput.value,
                address: addressInput.value,
                contact: contactInput.value,
                dateOfBirth: dobInput.value,
                gender: genderInput.value,
                citizenship: citizenshipInput.value,
                studentLevel: studentLevelInput.value,
                program: programSelect.value,
                subprogram: subprogramSelect.value,
                campus: campusSelect.value,
            };
            try {
                const successMessage = await viewModel.submitForm(formData);
                showModal(successMessage, true);
                form.reset(); // Clear form on success
                // Reset dropdowns to their initial state
                populateSelect(programSelect, viewModel.programs, "Select program");
                populateSelect(subprogramSelect, [], "Select program first...");
                subprogramSelect.disabled = true;
                populateSelect(campusSelect, viewModel.campuses, "Select campus");
                form.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
                form.querySelectorAll('.validation-error').forEach(el => el.textContent = '');

            } catch (error) {
                showModal(error, false);
            }
        } else {
            showModal("Please correct the errors in the form.", false);
        }
        registerButton.disabled = false;
        registerButton.textContent = 'Register';
    });

    clearButton.addEventListener('click', () => {
        form.reset();
        // Reset dropdowns and validation states
        populateSelect(programSelect, viewModel.programs, "Select program");
        populateSelect(subprogramSelect, [], "Select program first...");
        subprogramSelect.disabled = true;
        populateSelect(campusSelect, viewModel.campuses, "Select campus");
        form.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
        form.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        firstNameInput.focus(); // Focus on the first field
    });

    if (closeButton) {
        closeButton.addEventListener('click', hideModal);
    }
    // Close modal if clicked outside the content
    messageModal.addEventListener('click', (event) => {
        if (event.target === messageModal) {
            hideModal();
        }
    });


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
            subprogramSelect.disabled = true; // Initially disabled
            showForm();
        } catch (error) {
            console.error("Initialization error:", error);
            showError(error.message || "Unknown error occurred.");
        }
    }

    initializePage();
});
