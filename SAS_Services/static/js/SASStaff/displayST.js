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

    function toggleEditMode(enable) {
        const editableFields = editForm.querySelectorAll('input:not([type="hidden"]), select');
        const addressFields = document.querySelectorAll('.detail-grid input[name^="edit-"]');
        const addressDisplay = document.querySelector('.address-grid');
        const addressEditForm = document.querySelector('.detail-grid[style="display: none;"]');
        const emergencyContactFields = document.querySelectorAll('.emergency-contact input');
        const documentControls = document.querySelectorAll('.doc-action-btn, .doc-file-input, .doc-select');

        if (enable) {
            // Store original values before enabling edit mode
        editableFields.forEach(field => {
                field.readOnly = false;
                field.disabled = false;
                originalFieldValues[field.name] = field.value;
            });

            // Show edit form for address and hide display grid
            if (addressDisplay && addressEditForm) {
                addressDisplay.style.display = 'none';
                addressEditForm.style.display = 'grid';
            }

            // Enable address fields
            addressFields.forEach(field => {
                field.readOnly = false;
                field.disabled = false;
                originalFieldValues[field.name] = field.value;
            });

            // Enable emergency contact fields
            emergencyContactFields.forEach(field => {
                field.readOnly = false;
                field.disabled = false;
                originalFieldValues[field.name] = field.value;
            });

            // Enable document controls
            documentControls.forEach(control => {
                control.disabled = false;
            });

            editButton.style.display = 'none';
            saveButton.style.display = 'inline-flex';
            cancelButton.style.display = 'inline-flex';
            if (disableButton) disableButton.style.display = 'none';
        } else {
            // Restore original values and disable fields
            editableFields.forEach(field => {
                field.readOnly = true;
                field.disabled = true;
                if (originalFieldValues.hasOwnProperty(field.name)) {
                    field.value = originalFieldValues[field.name];
                }
            });

            // Show address display grid and hide edit form
            if (addressDisplay && addressEditForm) {
                addressDisplay.style.display = 'grid';
                addressEditForm.style.display = 'none';
            }

            // Disable address fields
            addressFields.forEach(field => {
                field.readOnly = true;
                field.disabled = true;
                if (originalFieldValues.hasOwnProperty(field.name)) {
                    field.value = originalFieldValues[field.name];
                }
            });

            // Disable emergency contact fields
            emergencyContactFields.forEach(field => {
                field.readOnly = true;
                field.disabled = true;
                if (originalFieldValues.hasOwnProperty(field.name)) {
                    field.value = originalFieldValues[field.name];
                }
            });

            // Disable document controls
            documentControls.forEach(control => {
                control.disabled = true;
            });

            editButton.style.display = 'inline-flex';
            saveButton.style.display = 'none';
            cancelButton.style.display = 'none';
            if (disableButton) disableButton.style.display = 'inline-flex';
        }
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

    function validateField(field) {
        console.log(`Validating field: ${field.id}`);
        let isValid = true;
        let errorMessage = '';

        // Required field validation
        if (field.required && !field.value.trim()) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Date validation for visa expiry
        if (field.id === 'edit-visa-expiry' && field.value) {
            // No validation needed for visa expiry date
            isValid = true;
            errorMessage = '';
        }

        // Academic program validation
        if (field.id === 'edit-program') {
            const studentLevel = document.getElementById('edit-student-level')?.value?.toLowerCase() || '';
            const programValue = field.value.toLowerCase();
            
            if (studentLevel.includes('bachelor')) {
                if (!(programValue.startsWith('bachelor of ') || 
                      programValue.startsWith('bachelor in ') || 
                      programValue.startsWith('bachelors of ') || 
                      programValue.startsWith('bachelors in '))) {
                isValid = false;
                    errorMessage = 'Program must start with Bachelor/Bachelors of/in for the selected level';
                }
            }
        }

        // Update UI
        const fieldContainer = field.closest('.form-group') || field.closest('.detail-item');
        const errorDisplay = fieldContainer?.querySelector('.validation-error');
        
        if (errorDisplay) {
            errorDisplay.textContent = errorMessage;
            errorDisplay.style.display = errorMessage ? 'block' : 'none';
        }
        
        field.classList.toggle('invalid', !isValid);
        
        console.log(`Validation result for ${field.id}: ${isValid}`);
        return isValid;
    }

    function validateAcademicSection() {
        console.log('Starting Academic Validation');
        const level = document.getElementById('edit-student-level')?.value;
        const programType = document.getElementById('edit-program-type')?.value;
        const program = document.getElementById('edit-program')?.value;

        console.log(`Academic Validation - Level: "${level}", Program Type: "${programType}", Program: "${program}"`);

        let isValid = true;

        // Validate program name based on level
        if (level?.toLowerCase().includes('bachelor')) {
            const programLower = program?.toLowerCase() || '';
            if (!programLower.startsWith('bachelor') && !programLower.startsWith('bachelors')) {
                console.log('Program Name Prefix ERROR. Level:', level, 'Program:', program);
                isValid = false;
                
                const programField = document.getElementById('edit-program');
                if (programField) {
                    const fieldContainer = programField.closest('.form-group');
                    const errorDisplay = fieldContainer?.querySelector('.validation-error');
                    if (errorDisplay) {
                        errorDisplay.textContent = 'Program must start with Bachelor/Bachelors for the selected level';
                        errorDisplay.style.display = 'block';
                    }
                    programField.classList.add('invalid');
                }
            }
        }

        console.log('After All Academic Validations, isValid:', isValid);
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
        }

        // Rule 2: If Student Level is Cert, Dip, Master, PG Dip, Program Type must be Prescribed.
        if (nonBachelorLevelsRequiringPrescribed.some(level => studentLevelLower.includes(level))) {
            if (currentProgramType !== "Prescribed Program") {
                console.log("Validation Error: Non-Bachelor (Cert, Dip, etc.) selected, but Program Type is not Prescribed.");
                validateField(programTypeSelect, true, `For ${currentStudentLevel}, Program Type must be 'Prescribed Program'.`);
                isOverallFormValid = false;
            }
        }

        // Rule 3: Program Name prefix validation
        if (programNameSelect && currentProgramName && currentStudentLevel) {
            const progNameLower = currentProgramName.toLowerCase();
            let prefixError = false;
            let expectedPrefix = "";

            if (studentLevelLower === "certificate" && !progNameLower.startsWith("certificate in ")) {
                prefixError = true;
                expectedPrefix = "Certificate in";
            }
            else if (studentLevelLower === "diploma" && !progNameLower.startsWith("diploma in ")) {
                prefixError = true;
                expectedPrefix = "Diploma in";
            }
            else if (studentLevelLower.includes("bachelor")) {
                if (!(progNameLower.startsWith("bachelor of ") || 
                      progNameLower.startsWith("bachelor in ") || 
                      progNameLower.startsWith("bachelors of ") || 
                      progNameLower.startsWith("bachelors in "))) {
                    prefixError = true;
                    expectedPrefix = "Bachelor/Bachelors of/in";
                }
            }
            else if (studentLevelLower.includes("master")) {
                if (!(progNameLower.startsWith("masters in ") || progNameLower.startsWith("master of "))) {
                    prefixError = true;
                    expectedPrefix = "Master(s) in/of";
                }
            }
            else if (studentLevelLower === "postgraduate diploma" && !progNameLower.startsWith("postgraduate diploma in ")) {
                prefixError = true;
                expectedPrefix = "Postgraduate Diploma in";
            }

            if (prefixError) {
                console.log(`Program Name Prefix ERROR. Level: "${studentLevelLower}", Program: "${progNameLower}". Expected prefix: "${expectedPrefix}"`);
                const programNameErrorSpan = programNameSelect.closest('.detail-item')?.querySelector('.validation-error');
                if (programNameErrorSpan) {
                    programNameErrorSpan.textContent = `Program name must start with '${expectedPrefix}...' for the selected student level.`;
                    programNameErrorSpan.style.display = 'block';
                }
                programNameSelect.classList.add('invalid');
                isOverallFormValid = false;
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

        try {
            // First, save the student details
            const response = await fetch(`/sas-staff/update-student/${STUDENT_ID}`, {
                method: 'POST',
                body: formDataToSubmit
            });

            const result = await response.json();
            if (result.status !== 'success') {
                throw new Error(result.message || 'Failed to save student details');
            }

            // Then, handle document uploads
            const documentFormData = new FormData();

            // Add birth certificate if selected
            const birthCertInput = document.getElementById('birth-certificate');
            if (birthCertInput?.files?.length > 0) {
                documentFormData.append('birth_certificate', birthCertInput.files[0]);
            }

            // Add valid ID if selected
            const validIdInput = document.getElementById('valid-id');
            const idTypeSelect = document.querySelector('.id-type-select');
            if (validIdInput?.files?.length > 0) {
                documentFormData.append('valid_id', validIdInput.files[0]);
                if (idTypeSelect) {
                    documentFormData.append('id_type', idTypeSelect.value);
                }
            }

            // Add academic transcript if selected
            const transcriptInput = document.getElementById('academic-transcript');
            const transcriptTypeSelect = document.querySelector('.transcript-type-select');
            if (transcriptInput?.files?.length > 0) {
                documentFormData.append('academic_transcript', transcriptInput.files[0]);
                if (transcriptTypeSelect) {
                    documentFormData.append('transcript_type', transcriptTypeSelect.value);
                }
            }

            // Only upload documents if any files were selected
            if (birthCertInput?.files?.length > 0 || validIdInput?.files?.length > 0 || transcriptInput?.files?.length > 0) {
                const docResponse = await fetch(`/sas-staff/upload-document/${STUDENT_ID}`, {
                    method: 'POST',
                    body: documentFormData
                });

                const docResult = await docResponse.json();
                if (docResult.status !== 'success') {
                    throw new Error(docResult.message || 'Failed to upload documents');
                }
            }

            showSnackbar("Changes saved successfully", true);
            toggleEditMode(false);

        } catch (error) {
            console.error('Error:', error);
            showSnackbar(error.message || "An error occurred while saving changes", false);
        } finally {
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<span class="material-icons">save</span> Save Changes';
            }
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
        editForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            console.log("Form submission started");
            
            updateSubprogramEditUI(); 
            if (!validateForm()) {
                console.log("Form validation failed");
                showSnackbar("Please correct the errors highlighted in the form.", false);
                return;
            }

            formDataToSubmit = new FormData(editForm);
            
            try {
                if(saveButton) {
                    saveButton.disabled = true;
                    saveButton.innerHTML = '<span class="material-icons">hourglass_top</span> Saving...';
                }

                const updateUrl = `/sas-staff/update-student/${STUDENT_ID}`;
                const response = await fetch(updateUrl, { 
                    method: 'POST', 
                    body: formDataToSubmit,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }

                const result = await response.json();
                
                if (result.status === 'success') {
                    showSnackbar(result.message || "Student details updated successfully!", true);
                    toggleEditMode(false);
                    
                    // Wait for snackbar to show before reloading
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(result.message || "Failed to update student details");
                }
            } catch (error) {
                console.error("Error saving student details:", error);
                showSnackbar(`Error saving changes: ${error.message}`, false);
            } finally {
                if(saveButton) {
                    saveButton.disabled = false;
                    saveButton.innerHTML = '<span class="material-icons">save</span> Save Changes';
                }
                formDataToSubmit = null;
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

    // Document verification handling
    document.querySelectorAll('.btn-view-doc').forEach(button => {
        button.addEventListener('click', async (e) => {
            const docType = e.target.dataset.docType;
            const docId = e.target.dataset.docId;
            
            if (!docType || !docId) {
                showSnackbar('Invalid document information', false);
                return;
            }

            try {
                const response = await fetch(`/sas-staff/verify-document/${docType}/${docId}`, {
                    method: 'POST'
                });

                const result = await response.json();
                if (result.status === 'success') {
                    showSnackbar('Document verified successfully', true);
                    // Update status display
                    const statusSpan = e.target.closest('.document-info').querySelector('.document-status');
                    if (statusSpan) {
                        statusSpan.textContent = 'Status: Verified';
                    }
                } else {
                    throw new Error(result.message || 'Failed to verify document');
                }
            } catch (error) {
                console.error('Error:', error);
                showSnackbar(error.message || 'An error occurred while verifying the document', false);
            }
        });
    });

    // Document removal handling
    document.querySelectorAll('.btn-remove-doc').forEach(button => {
        button.addEventListener('click', async (e) => {
            const docType = e.target.dataset.docType;
            if (!docType || !STUDENT_ID) {
                showSnackbar('Invalid document information', false);
                return;
            }

            if (!confirm('Are you sure you want to remove this document?')) {
                return;
            }

            try {
                const response = await fetch(`/sas-staff/remove-document/${docType}/${STUDENT_ID}`, {
                    method: 'POST'
                });

                const result = await response.json();
                if (result.status === 'success') {
                    showSnackbar('Document removed successfully', true);
                    // Remove document info display
                    const docInfo = e.target.closest('.document-info');
                    if (docInfo) {
                        docInfo.remove();
                    }
                    // Update upload button text
                    const uploadBtn = e.target.closest('.document-item').querySelector('.btn-upload-doc');
                    if (uploadBtn) {
                        uploadBtn.textContent = 'Upload';
                    }
                } else {
                    throw new Error(result.message || 'Failed to remove document');
                }
            } catch (error) {
                console.error('Error:', error);
                showSnackbar(error.message || 'An error occurred while removing the document', false);
            }
        });
    });

    // Add event listeners for file inputs
    document.addEventListener('DOMContentLoaded', () => {
        // Birth Certificate upload
        const birthCertInput = document.getElementById('birth-certificate');
        if (birthCertInput) {
            birthCertInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    console.log('Uploading birth certificate:', file.name);
                    try {
                        await uploadDocument(STUDENT_ID, 'birth_certificate', file);
                        location.reload(); // Reload to show updated document status
                    } catch (error) {
                        console.error('Error uploading birth certificate:', error);
                        showSnackbar('Error uploading birth certificate: ' + error.message, false);
                    }
                }
            });
        }

        // Valid ID upload
        const validIdInput = document.getElementById('valid-id');
        const idTypeSelect = document.getElementById('id-type');
        if (validIdInput) {
            validIdInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    if (!idTypeSelect || !idTypeSelect.value) {
                        showSnackbar('Please select an ID type first', false);
                        e.target.value = ''; // Clear the file input
                        return;
                    }
                    console.log('Uploading valid ID:', file.name);
                    try {
                        await uploadDocument(STUDENT_ID, 'valid_id', file, { id_type: idTypeSelect.value });
                        location.reload(); // Reload to show updated document status
                    } catch (error) {
                        console.error('Error uploading valid ID:', error);
                        showSnackbar('Error uploading valid ID: ' + error.message, false);
                    }
                }
            });
        }

        // Academic Transcript upload
        const transcriptInput = document.getElementById('academic-transcript');
        const transcriptTypeSelect = document.getElementById('transcript-type');
        if (transcriptInput) {
            transcriptInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    if (!transcriptTypeSelect || !transcriptTypeSelect.value) {
                        showSnackbar('Please select a transcript type first', false);
                        e.target.value = ''; // Clear the file input
                        return;
                    }
                    console.log('Uploading academic transcript:', file.name);
                    try {
                        await uploadDocument(STUDENT_ID, 'academic_transcript', file, { transcript_type: transcriptTypeSelect.value });
                        location.reload(); // Reload to show updated document status
                    } catch (error) {
                        console.error('Error uploading academic transcript:', error);
                        showSnackbar('Error uploading academic transcript: ' + error.message, false);
                    }
                }
            });
        }
    });

    // Upload document function
    async function uploadDocument(studentId, docType, file, additionalData = {}) {
        try {
            console.log('Starting document upload:', { studentId, docType, fileName: file.name, additionalData });
            
            const formData = new FormData();
            formData.append(docType, file);
            
            // Add additional data if provided
            for (const [key, value] of Object.entries(additionalData)) {
                formData.append(key, value);
            }

            console.log('Sending request to:', `/sas-staff/upload-document/${studentId}`);
            const response = await fetch(`/sas-staff/upload-document/${studentId}`, {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);

            if (!response.ok) {
                throw new Error(result.message || 'Error uploading document');
            }

            showSnackbar('Document uploaded successfully', true);
            return result;
        } catch (error) {
            console.error('Error in uploadDocument:', error);
            throw error;
        }
    }

    // Update toggleEditMode to handle document controls
    const originalToggleEditMode = toggleEditMode;
    toggleEditMode = function(enable) {
        originalToggleEditMode(enable);
        
        // Enable/disable document controls
        const documentControls = document.querySelectorAll('.doc-action-btn, .doc-file-input, .doc-select');
        documentControls.forEach(control => {
            control.disabled = !enable;
        });
    };

    // Initial setup
    toggleEditMode(false);

    console.log("displayST.js: Initialized with full validation logic.");

    // Add event listeners for upload buttons
    const uploadButtons = document.querySelectorAll('.btn-upload-doc');
    uploadButtons.forEach(button => {
        button.addEventListener('click', () => {
            const docType = button.getAttribute('data-doc-type');
            let fileInput;
            switch (docType) {
                case 'birth_certificate':
                    fileInput = document.getElementById('birth-certificate');
                    break;
                case 'valid_id':
                    fileInput = document.getElementById('valid-id');
                    break;
                case 'academic_transcript':
                    fileInput = document.getElementById('academic-transcript');
                    break;
            }
            if (fileInput) {
                fileInput.click();
            }
        });
    });

    // Add event listeners for view buttons
    const viewButtons = document.querySelectorAll('.btn-view-doc');
    viewButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const docType = button.getAttribute('data-doc-type');
            const docId = button.getAttribute('data-doc-id');
            if (docType && docId) {
                window.open(`/sas-staff/view-document/${docType}/${docId}`, '_blank');
            }
        });
    });

    // Add event listeners for remove buttons
    const removeButtons = document.querySelectorAll('.btn-remove-doc');
    removeButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const docType = button.getAttribute('data-doc-type');
            if (docType && STUDENT_ID) {
                if (confirm('Are you sure you want to remove this document?')) {
                    try {
                        const response = await fetch(`/sas-staff/remove-document/${docType}/${STUDENT_ID}`, {
                            method: 'POST'
                        });
                        const result = await response.json();
                        if (response.ok) {
                            showSnackbar('Document removed successfully', true);
                            window.location.reload();
                        } else {
                            throw new Error(result.message || 'Error removing document');
                        }
                    } catch (error) {
                        console.error('Error removing document:', error);
                        showSnackbar(error.message || 'Error removing document', false);
                    }
                }
            }
        });
    });
});
