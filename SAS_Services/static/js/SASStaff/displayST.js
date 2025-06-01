// static/js/SASStaff/displayST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("displayST.js: DOMContentLoaded. STUDENT_ID:", typeof STUDENT_ID !== 'undefined' ? STUDENT_ID : 'NOT DEFINED');
    // console.log("ORIGINAL_STUDENT_DATA:", typeof ORIGINAL_STUDENT_DATA !== 'undefined' ? ORIGINAL_STUDENT_DATA : 'NOT DEFINED');
    // console.log("ALL_SUBPROGRAMMES:", typeof ALL_SUBPROGRAMMES !== 'undefined' ? ALL_SUBPROGRAMMES : 'NOT DEFINED');

    const editForm = document.getElementById('edit-student-details-form');

    if (!editForm || (typeof STUDENT_ID === 'undefined' || !STUDENT_ID || STUDENT_ID.trim() === "")) {
        console.warn("displayST.js: Edit form not found or STUDENT_ID is missing/empty. Edit/disable functionality will be limited or inactive.");
        const editBtn = document.getElementById('edit-student-details-btn');
        const saveBtn = document.getElementById('save-student-changes-btn');
        const cancelBtn = document.getElementById('cancel-edit-student-btn');
        const disableBtn = document.getElementById('disable-student-btn');
        if(editBtn) editBtn.style.display = 'none';
        if(saveBtn) saveBtn.style.display = 'none';
        if(cancelBtn) cancelBtn.style.display = 'none';
        if(disableBtn) disableBtn.style.display = 'none';
        return;
    }

    const editButton = document.getElementById('edit-student-details-btn');
    const saveButton = document.getElementById('save-student-changes-btn');
    const cancelButton = document.getElementById('cancel-edit-student-btn');
    const disableButton = document.getElementById('disable-student-btn');
    const snackbar = document.getElementById('snackbar');

    const saveChangesConfirmDialog = document.getElementById('save-changes-confirm-dialog');
    const cancelSaveActionButton = document.getElementById('cancel-save-action-btn');
    const confirmFinalSaveActionButton = document.getElementById('confirm-final-save-action-btn');

    // Form field references
    const studentLevelSelect = document.getElementById('edit-student-level');
    const programNameSelect = document.getElementById('edit-program-name');
    const programTypeSelect = document.getElementById('edit-program-type-name');
    const subprogram1Group = document.getElementById('edit-subprogram1-group');
    const subprogram1Select = document.getElementById('edit-subprogram1');
    const subprogram1RequiredAsterisk = document.getElementById('edit-subprogram1-required-asterisk');
    const subprogram2Group = document.getElementById('edit-subprogram2-group');
    const subprogram2Select = document.getElementById('edit-subprogram2');
    const subprogram2RequiredAsterisk = document.getElementById('edit-subprogram2-required-asterisk');

    const editableFields = editForm.querySelectorAll('input:not([type="hidden"]), select');
    let originalFieldValues = {};
    let formDataToSubmit = null;

    function showSnackbar(message, isSuccess = true) {
        if (!snackbar) return;
        snackbar.textContent = message;
        snackbar.className = 'snackbar show';
        snackbar.classList.add(isSuccess ? 'success' : 'error');
        setTimeout(() => { snackbar.className = 'snackbar'; }, 3000);
    }

    function showModal(modalElement) {
        if (!modalElement) { console.warn("Attempted to show null modal"); return; }
        modalElement.style.display = 'flex';
        setTimeout(() => modalElement.classList.add('active'), 10);
    }

    function hideModal(modalElement) {
        if (!modalElement) { console.warn("Attempted to hide null modal"); return; }
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) {
                modalElement.style.display = 'none';
            }
        }, 300);
     }

    function updateSubprogramEditUI() {
        const selectedStudentLevel = studentLevelSelect ? studentLevelSelect.value.toLowerCase() : "";
        const selectedProgramType = programTypeSelect ? programTypeSelect.value : "";
        const isBachelorLevel = selectedStudentLevel.includes("bachelor");

        let showSub1 = false, requireSub1 = false, showSub2 = false, requireSub2 = false;

        if (isBachelorLevel) {
            if (selectedProgramType === "Single Major") { showSub1 = true; requireSub1 = true; }
            else if (selectedProgramType === "Double Major") { showSub1 = true; requireSub1 = true; showSub2 = true; requireSub2 = true; }
        }

        if (subprogram1Group) subprogram1Group.style.display = showSub1 ? 'block' : 'none';
        if (subprogram1Select) {
            subprogram1Select.required = requireSub1;
            if (!showSub1) {
                subprogram1Select.value = '';
                validateField(subprogram1Select, false); // Clear validation error if hiding
            }
        }
        if (subprogram1RequiredAsterisk) subprogram1RequiredAsterisk.style.display = requireSub1 ? 'inline' : 'none';

        if (subprogram2Group) subprogram2Group.style.display = showSub2 ? 'block' : 'none';
        if (subprogram2Select) {
            subprogram2Select.required = requireSub2;
            if (!showSub2) {
                subprogram2Select.value = '';
                validateField(subprogram2Select, false); // Clear validation error if hiding
            }
        }
        if (subprogram2RequiredAsterisk) subprogram2RequiredAsterisk.style.display = requireSub2 ? 'inline' : 'none';
    }

    function toggleEditMode(isEditing) {
        editableFields.forEach(field => {
            field.tagName === 'SELECT' ? (field.disabled = !isEditing) : (field.readOnly = !isEditing);
            if (!isEditing) {
                field.classList.remove('invalid');
                const errorSpan = field.closest('.detail-item')?.querySelector('.validation-error');
                if (errorSpan) errorSpan.textContent = '';
            }
        });
        if (isEditing) {
            if(editButton) editButton.style.display = 'none';
            if(disableButton) disableButton.style.display = 'none';
            if(saveButton) saveButton.style.display = 'inline-block';
            if(cancelButton) cancelButton.style.display = 'inline-block';
            originalFieldValues = {};
            editableFields.forEach(field => { originalFieldValues[field.name] = field.value; });
        } else {
            if(editButton) editButton.style.display = 'inline-block';
            if(disableButton) disableButton.style.display = 'inline-block';
            if(saveButton) saveButton.style.display = 'none';
            if(cancelButton) cancelButton.style.display = 'none';
        }
        updateSubprogramEditUI();
    }

    function revertFormChanges() {
        if (typeof ORIGINAL_STUDENT_DATA === 'object' && ORIGINAL_STUDENT_DATA && Object.keys(ORIGINAL_STUDENT_DATA).length > 0) {
            const dataMap = {
                'firstName': ORIGINAL_STUDENT_DATA.first_name, 'middleName': ORIGINAL_STUDENT_DATA.middle_name,
                'lastName': ORIGINAL_STUDENT_DATA.last_name, 'dateOfBirth': ORIGINAL_STUDENT_DATA.date_of_birth,
                'gender': ORIGINAL_STUDENT_DATA.gender, 'citizenship': ORIGINAL_STUDENT_DATA.citizenship,
                'address': ORIGINAL_STUDENT_DATA.address, 'contact': ORIGINAL_STUDENT_DATA.contact,
                'email': ORIGINAL_STUDENT_DATA.email, 'studentLevel': ORIGINAL_STUDENT_DATA.student_level,
                'programName': ORIGINAL_STUDENT_DATA.program_name, 'campusName': ORIGINAL_STUDENT_DATA.campus_name,
                'programTypeName': ORIGINAL_STUDENT_DATA.program_type_name,
                'subprogram1': ORIGINAL_STUDENT_DATA.subprogram1 || '',
                'subprogram2': ORIGINAL_STUDENT_DATA.subprogram2 || ''
            };
            editableFields.forEach(field => {
                if (dataMap.hasOwnProperty(field.name)) {
                    field.value = dataMap[field.name] || '';
                }
            });
        }
        updateSubprogramEditUI();
    }

    function validateField(inputElement, showErrorMsg = true) {
        if (!inputElement) return true;
        const group = inputElement.closest('.detail-item');
        const errorElement = group?.querySelector('.validation-error');
        let isValid = true;
        let errorMessage = "";
        const isEffectivelyRequired = inputElement.required &&
                                      !inputElement.disabled &&
                                      !inputElement.readOnly &&
                                      group && window.getComputedStyle(group).display !== 'none';

        if (isEffectivelyRequired && String(inputElement.value).trim() === '') {
            isValid = false;
            errorMessage = "This field is required.";
        }
        
        if (isValid && inputElement.id === 'edit-contact' && inputElement.value.trim() !== '') {
             const regex = /^679-\d{7}$/;
             if (!regex.test(inputElement.value)) {
                 isValid = false;
                 errorMessage = "Invalid contact. Expected: 679-XXXXXXX";
             }
        }
        if (isValid && inputElement.type === 'email' && inputElement.value.trim() !== '') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if(!emailRegex.test(inputElement.value)){
                isValid = false;
                errorMessage = "Invalid email format.";
            }
        }
        if (isValid && inputElement.type === 'date' && inputElement.value) {
            const selectedDate = new Date(inputElement.value);
            const today = new Date(); today.setHours(0,0,0,0);
            const minBirthYear = today.getFullYear() - 100;
            const maxBirthYear = today.getFullYear() - 15;
            const minDate = new Date(minBirthYear, 0, 1);
            const maxDate = new Date(maxBirthYear, today.getMonth(), today.getDate());

            if (selectedDate > maxDate) {
                isValid = false; errorMessage = "Student must be at least 15 years old.";
            } else if (selectedDate < minDate) {
                isValid = false; errorMessage = "Date of birth is too far in the past.";
            } else if (selectedDate > today) {
                isValid = false; errorMessage = "Date of birth cannot be in the future.";
            }
        }

        if (errorElement) { errorElement.textContent = showErrorMsg ? errorMessage : ""; }
        inputElement.classList.toggle('invalid', !isValid && showErrorMsg);
        return isValid;
    }

    function validateForm() {
        console.log("--- Starting Full Form Validation ---");
        let isOverallFormValid = true;
        if (!editForm) { console.error("validateForm: editForm not found!"); return false; }

        console.log("Validating general required fields...");
        editableFields.forEach(field => {
            if (!validateField(field)) {
                console.log(`Field ${field.id || field.name} failed general validation.`);
                isOverallFormValid = false;
            }
        });
        console.log(`After general validation, isOverallFormValid: ${isOverallFormValid}`);

        const currentStudentLevel = studentLevelSelect ? studentLevelSelect.value : "";
        const currentProgramType = programTypeSelect ? programTypeSelect.value : "";
        const currentProgramName = programNameSelect ? programNameSelect.value : "";
        console.log(`Academic Validation - Level: "${currentStudentLevel}", Program Type: "${currentProgramType}", Program: "${currentProgramName}"`);

        const studentLevelLower = currentStudentLevel.toLowerCase();
        const nonBachelorLevelsRequiringPrescribed = ["certificate", "diploma", "master", "postgraduate diploma"];

        // Rule 1: If Program Type is Single/Double Major, Student Level must be Bachelor.
        if ((currentProgramType === "Single Major" || currentProgramType === "Double Major") && !studentLevelLower.includes("bachelor")) {
            console.log("Validation Error: Single/Double Major selected, but level is not Bachelor.");
            validateField(studentLevelSelect, true, "Single/Double Major is only for Bachelor level students.");
            isOverallFormValid = false;
        } else if (studentLevelSelect && studentLevelSelect.classList.contains('invalid') && studentLevelSelect.closest('.detail-item').querySelector('.validation-error').textContent.includes("only for Bachelor level")) {
            // Clear this specific error if condition no longer met, but re-validate for general required.
            if(validateField(studentLevelSelect)) { // If it's valid now (e.g. filled and rule met)
                 studentLevelSelect.classList.remove('invalid'); // Might still be invalid for other reasons
                 studentLevelSelect.closest('.detail-item').querySelector('.validation-error').textContent = '';
            } else {
                isOverallFormValid = false; // Still invalid for other reasons
            }
        }

        // Rule 2: If Student Level is Cert, Dip, Master, PG Dip, Program Type must be Prescribed.
        if (nonBachelorLevelsRequiringPrescribed.some(level => studentLevelLower.includes(level))) {
            if (currentProgramType !== "Prescribed Program") {
                console.log("Validation Error: Non-Bachelor (Cert, Dip, etc.) selected, but Program Type is not Prescribed.");
                validateField(programTypeSelect, true, `For ${currentStudentLevel}, Program Type must be 'Prescribed Program'.`);
                isOverallFormValid = false;
            } else if (programTypeSelect && programTypeSelect.classList.contains('invalid') && programTypeSelect.closest('.detail-item').querySelector('.validation-error').textContent.includes("must be 'Prescribed Program'")) {
                 if(validateField(programTypeSelect)){
                    programTypeSelect.classList.remove('invalid');
                    programTypeSelect.closest('.detail-item').querySelector('.validation-error').textContent = '';
                 } else {
                    isOverallFormValid = false;
                 }
            }
        }


        // Rule 3: Program Name prefix validation (remains the same)
        if (programNameSelect && currentProgramName && currentStudentLevel) {
            // ... (Your existing program name prefix validation logic from message #54) ...
            // Ensure it also sets isOverallFormValid = false if prefixError is true.
            let prefixError = false;
            const progNameLower = currentProgramName.toLowerCase();
            let expectedPrefix = "";

            if (studentLevelLower === "certificate" && !progNameLower.startsWith("certificate in ")) { prefixError = true; expectedPrefix = "Certificate in"; }
            else if (studentLevelLower === "diploma" && !progNameLower.startsWith("diploma in ")) { prefixError = true; expectedPrefix = "Diploma in"; }
            else if (studentLevelLower.includes("bachelor")) { if (!(progNameLower.startsWith("bachelor of ") || progNameLower.startsWith("bachelor in "))) { prefixError = true; expectedPrefix = "Bachelor of/in"; } }
            else if (studentLevelLower.includes("master")) { if (!(progNameLower.startsWith("masters in ") || progNameLower.startsWith("master of "))) { prefixError = true; expectedPrefix = "Master(s) in/of"; } }
            else if (studentLevelLower === "postgraduate diploma") { if (!progNameLower.startsWith("postgraduate diploma in ")) { prefixError = true; expectedPrefix = "Postgraduate Diploma in"; } }
            
            const programNameErrorSpan = programNameSelect.closest('.detail-item')?.querySelector('.validation-error');
            if (prefixError) {
                console.log(`Program Name Prefix ERROR. Level: "${studentLevelLower}", Program: "${progNameLower}". Expected prefix: "${expectedPrefix}"`);
                if (programNameErrorSpan) programNameErrorSpan.textContent = `Program name must start with '${expectedPrefix}...' for the selected student level.`;
                programNameSelect.classList.add('invalid');
                isOverallFormValid = false;
            } else {
                if (programNameErrorSpan && programNameErrorSpan.textContent.includes("Program name must start with")) {
                    programNameErrorSpan.textContent = "";
                    if (validateField(programNameSelect)) {
                       programNameSelect.classList.remove('invalid');
                    } else {
                       isOverallFormValid = false;
                    }
                }
            }
        }
        console.log(`After All Academic Validations, isOverallFormValid: ${isOverallFormValid}`);
        console.log("--- Form Validation Complete ---");
        return isOverallFormValid;
    }

    async function proceedWithSavingChanges() {
        if (!formDataToSubmit) {
            console.error("No form data stored for submission.");
            showSnackbar("An error occurred, unable to save changes.", false);
            return;
        }

        if(saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="material-icons">hourglass_top</span> Saving...';
        }

        const updateUrl = `/sas-staff/update-student/${STUDENT_ID}`;

        try {
            const response = await fetch(updateUrl, { method: 'POST', body: formDataToSubmit });
            const result = await response.json();

            if (result.success) {
                showSnackbar(result.message || "Student details updated successfully!", true);
                toggleEditMode(false);
                
                const studentHeaderName = document.getElementById('student-header-name');
                if (studentHeaderName) {
                    studentHeaderName.textContent = `${formDataToSubmit.get('firstName')} ${formDataToSubmit.get('middleName') || ''} ${formDataToSubmit.get('lastName')}`.replace(/\s+/g, ' ').trim();
                }

                if (typeof ORIGINAL_STUDENT_DATA === 'object' && ORIGINAL_STUDENT_DATA !== null) {
                    const keyMap = {
                        'firstName': 'first_name', 'middleName': 'middle_name', 'lastName': 'last_name',
                        'dateOfBirth': 'date_of_birth', 'programName': 'program_name',
                        'studentLevel': 'student_level', 'campusName': 'campus_name',
                        'programTypeName': 'program_type_name', 'subprogram1': 'subprogram1', 'subprogram2': 'subprogram2',
                        'gender': 'gender', 'citizenship': 'citizenship', 'address': 'address',
                        'contact': 'contact', 'email': 'email'
                    };
                    for (let [formKey, value] of formDataToSubmit.entries()) {
                        const originalDataKey = keyMap[formKey] || formKey;
                        ORIGINAL_STUDENT_DATA[originalDataKey] = value; // Add or update
                    }
                }
            } else {
                showSnackbar(result.message || "Failed to update student details.", false);
            }
        } catch (error) {
            console.error("Error saving student details:", error);
            showSnackbar("An error occurred while saving. Please try again.", false);
        } finally {
            if(saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<span class="material-icons">save</span> Save Changes';
            }
            formDataToSubmit = null;
        }
    }

    // --- Event Listeners ---
    if (editButton) {
        editButton.addEventListener('click', () => {
            if (!STUDENT_ID || STUDENT_ID.trim() === "") {
                console.error("Student ID is missing or empty. Cannot enable edit mode.");
                showSnackbar("Error: Student ID is missing. Cannot enable edit mode.", false);
                return;
            }
            toggleEditMode(true);
        });
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', () => {
            revertFormChanges();
            toggleEditMode(false);
        });
    }

    if (studentLevelSelect) {
        studentLevelSelect.addEventListener('change', () => {
            if (!studentLevelSelect.disabled) {
                 updateSubprogramEditUI();
                 validateField(studentLevelSelect);
                 if(programNameSelect) validateField(programNameSelect, true);
            }
        });
    }
    if (programTypeSelect) {
        programTypeSelect.addEventListener('change', () => {
             if (!programTypeSelect.disabled) {
                updateSubprogramEditUI();
                validateField(programTypeSelect);
             }
        });
    }
    if (programNameSelect) {
        programNameSelect.addEventListener('change', () => {
            if(!programNameSelect.disabled) {
                validateField(programNameSelect); // General validation first
                // Attempt to clear prefix error dynamically if it matches now
                const errorSpan = programNameSelect.closest('.detail-item')?.querySelector('.validation-error');
                if (errorSpan && errorSpan.textContent.includes("Program name must start with")) {
                    const currentStudentLevel = studentLevelSelect ? studentLevelSelect.value : "";
                    const currentProgramNameVal = programNameSelect.value; // Use .value
                    let prefixError = false;
                    const progNameLower = currentProgramNameVal.toLowerCase();
                    const levelLower = currentStudentLevel.toLowerCase();

                    if (levelLower === "certificate" && !progNameLower.startsWith("certificate in ")) prefixError = true;
                    else if (levelLower === "diploma" && !progNameLower.startsWith("diploma in ")) prefixError = true;
                    else if (levelLower.includes("bachelor")) { if (!(progNameLower.startsWith("bachelor of ") || progNameLower.startsWith("bachelor in "))) prefixError = true; }
                    else if (levelLower.includes("master")) { if (!(progNameLower.startsWith("masters in ") || progNameLower.startsWith("master of "))) prefixError = true; }
                    else if (levelLower === "postgraduate diploma") { if (!progNameLower.startsWith("postgraduate diploma in ")) prefixError = true; }

                    if (!prefixError) { // If prefix is now correct
                        if (validateField(programNameSelect)) { // And it's not empty if required
                             errorSpan.textContent = ""; // Clear the prefix error
                             programNameSelect.classList.remove('invalid');
                        }
                        // If validateField(programNameSelect) is false, it means it's empty and required, so error message from validateField remains.
                    }
                }
            }
        });
    }


    if (editForm && saveButton) {
        editForm.addEventListener('submit', (event) => {
            event.preventDefault();
            updateSubprogramEditUI(); 
            if (!validateForm()) {
                showSnackbar("Please correct the errors highlighted in the form.", false);
                return;
            }
            formDataToSubmit = new FormData(editForm);
            if(saveChangesConfirmDialog) showModal(saveChangesConfirmDialog);
            else { 
                console.warn("Save confirmation dialog not found, proceeding directly.");
                proceedWithSavingChanges(); 
            }
        });
    }
    
    if (cancelSaveActionButton && saveChangesConfirmDialog) {
        cancelSaveActionButton.addEventListener('click', () => {
            hideModal(saveChangesConfirmDialog);
            formDataToSubmit = null;
        });
    }
    if (confirmFinalSaveActionButton && saveChangesConfirmDialog) {
        confirmFinalSaveActionButton.addEventListener('click', () => {
            hideModal(saveChangesConfirmDialog);
            proceedWithSavingChanges();
        });
    }
    if (saveChangesConfirmDialog) {
        saveChangesConfirmDialog.addEventListener('click', (event) => {
            if (event.target === saveChangesConfirmDialog) {
                 hideModal(saveChangesConfirmDialog);
                 formDataToSubmit = null;
            }
        });
    }
    
    const localDisableStudentBtn = document.getElementById('disable-student-btn');
    const disableConfirmDialog = document.getElementById('disable-confirm-dialog');
    
    if (localDisableStudentBtn && disableConfirmDialog) {
        const cancelDisableBtn = disableConfirmDialog.querySelector('[data-action="cancel-disable"]');
        const confirmDisableBtn = disableConfirmDialog.querySelector('[data-action="confirm-disable"]');

        localDisableStudentBtn.addEventListener('click', () => {
             if (!STUDENT_ID || STUDENT_ID.trim() === "") {
                console.error("Student ID not found for disabling.");
                showSnackbar("Error: Student ID is missing.", false);
                return;
            }
            showModal(disableConfirmDialog);
        });

        if(cancelDisableBtn) cancelDisableBtn.addEventListener('click', () => hideModal(disableConfirmDialog));
        if(disableConfirmDialog) disableConfirmDialog.addEventListener('click', (e) => {if (e.target === disableConfirmDialog) hideModal(disableConfirmDialog);});

        if(confirmDisableBtn) confirmDisableBtn.addEventListener('click', () => {
            hideModal(disableConfirmDialog);
            console.log(`Confirm disable for student ID: ${STUDENT_ID}`);
            showSnackbar(`Mock: Disabling student ${STUDENT_ID}. Implement API call.`, true);
        });
    }

    // Initial setup
    toggleEditMode(false);

    console.log("displayST.js: Initialized with full validation logic.");
});
