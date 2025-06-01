// static/js/SASStaff/allST.js
document.addEventListener('DOMContentLoaded', () => {
    console.log("allST.js: DOMContentLoaded");

    const searchInput = document.getElementById('search-input-allST');
    const tableBody = document.getElementById('enrollments-table-body-allST');
    const noEnrollmentsMessage = document.getElementById('no-enrollments-message-allST');
    const tableContainer = document.getElementById('enrollments-table-container-allST');
    const loadingIndicator = document.getElementById('loading-indicator-allST');

    // Modal elements for Initial Grade Change Input
    const changeGradeModal = document.getElementById('change-grade-modal');
    const modalStudentName = document.getElementById('modal-student-name');
    const modalStudentId = document.getElementById('modal-student-id');
    const modalCourseCode = document.getElementById('modal-course-code');
    const modalCurrentGrade = document.getElementById('modal-current-grade');
    const newGradeInput = document.getElementById('new-grade-input');
    const cancelChangeGradeBtn = document.getElementById('cancel-change-grade');
    const confirmChangeGradeBtn = document.getElementById('confirm-change-grade');
    const gradeValidationError = changeGradeModal ? changeGradeModal.querySelector('.validation-error') : null;
    const changeGradeModalCloseBtn = changeGradeModal ? changeGradeModal.querySelector('.modal-close-button') : null;

    // Modal elements for Final Grade Change Confirmation
    const finalConfirmGradeModal = document.getElementById('final-confirm-grade-modal');
    const finalConfirmGradeMessage = document.getElementById('final-confirm-grade-message');
    const cancelFinalSaveBtn = document.getElementById('cancel-final-save');
    const confirmFinalSaveBtn = document.getElementById('confirm-final-save');
    const finalConfirmModalCloseBtn = finalConfirmGradeModal ? finalConfirmGradeModal.querySelector('.modal-close-button') : null;

    // Modal elements for Success Notification
    const successModal = document.getElementById('grade-change-success-modal');
    const successModalMessage = document.getElementById('grade-change-success-message');
    const successModalOkBtn = document.getElementById('grade-change-success-ok-btn');
    const successModalCloseBtn = successModal ? successModal.querySelector('.modal-close-button') : null;

    let currentChangeGradeData = null; // Stores { studentId, courseCode, studentFullName, currentGrade, newGrade }

    // Define accepted grades for validation
    const ACCEPTED_GRADES_LIST = ["A+", "A", "B+", "B", "C+", "C", "D", "E"];
    const ACCEPTED_GRADES_SET = new Set(ACCEPTED_GRADES_LIST);
    const ACCEPTED_GRADES_STRING = `{${ACCEPTED_GRADES_LIST.join(', ')}}`;


    // --- HELPER FUNCTION to update the Change Grade button's state ---
    function updateChangeGradeButtonState(buttonElement, newGradeValue) {
        if (!buttonElement) return;
        const hasActualGrade = newGradeValue && newGradeValue.trim() !== "" && newGradeValue.toUpperCase() !== "N/A";
        if (hasActualGrade) {
            buttonElement.disabled = false;
            buttonElement.removeAttribute('title');
        } else {
            buttonElement.disabled = true;
            buttonElement.title = "No grade initially given";
        }
    }

    // Initial display logic
    if (loadingIndicator) loadingIndicator.style.display = 'none';
    if (tableBody && tableBody.querySelector('tr td:not(.no-data-message)')) {
        if (tableContainer) tableContainer.style.display = 'block';
        if (noEnrollmentsMessage) noEnrollmentsMessage.style.display = 'none';
    } else if (tableBody) {
        if (tableContainer) tableContainer.style.display = 'none';
        if (noEnrollmentsMessage) {
            noEnrollmentsMessage.textContent = "No student enrollments to display.";
            noEnrollmentsMessage.style.display = 'block';
        }
    }

    // Search/Filter functionality
    if (searchInput && tableBody) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            const rows = tableBody.getElementsByTagName('tr');
            let visibleRows = 0;
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                if (row.querySelector('.no-data-message')) {
                    row.style.display = (searchTerm === "" && rows.length === 1) ? "" : "none";
                    continue;
                }
                const studentId = row.dataset.studentId?.toLowerCase() || "";
                const fullName = row.dataset.fullName?.toLowerCase() || "";
                const course = row.dataset.course?.toLowerCase() || "";
                if (studentId.includes(searchTerm) || fullName.includes(searchTerm) || course.includes(searchTerm)) {
                    row.style.display = "";
                    visibleRows++;
                } else {
                    row.style.display = "none";
                }
            }
            if (noEnrollmentsMessage) {
                const hasActualDataRows = Array.from(rows).some(row => !row.querySelector('.no-data-message'));
                if (visibleRows === 0 && hasActualDataRows) {
                    noEnrollmentsMessage.textContent = "No enrollments match your search.";
                    noEnrollmentsMessage.style.display = 'block';
                } else if (!hasActualDataRows && rows.length <= 1) {
                    noEnrollmentsMessage.textContent = "No student enrollments to display.";
                    noEnrollmentsMessage.style.display = 'block';
                } else {
                    noEnrollmentsMessage.style.display = 'none';
                }
            }
        });
    }

    // Modal show/hide utility
    function showModal(modalElement) {
        if (!modalElement) { console.error("Attempted to show null modal:", modalElement); return; }
        modalElement.style.display = 'flex';
        setTimeout(() => modalElement.classList.add('active'), 10);
    }

    function hideModal(modalElement) {
        if (!modalElement) { console.error("Attempted to hide null modal:", modalElement); return; }
        modalElement.classList.remove('active');
        setTimeout(() => {
            if (!modalElement.classList.contains('active')) {
                modalElement.style.display = 'none';
            }
        }, 300);
    }

    // Event listener for "Change Grade" buttons
    if (tableBody) {
        tableBody.addEventListener('click', function(event) {
            const target = event.target.closest('.change-grade-btn');
            if (target && !target.disabled) {
                const studentId = target.dataset.studentId;
                const courseFull = target.closest('tr')?.dataset.course || "Unknown Course";
                const courseCode = target.dataset.courseCode;
                const studentFullName = target.closest('tr')?.dataset.fullName || "Selected Student";
                const currentGrade = target.dataset.currentGrade || "";
                currentChangeGradeData = { studentId, courseCode, studentFullName, currentGrade, newGrade: "" };

                if (modalStudentName) modalStudentName.textContent = studentFullName;
                if (modalStudentId) modalStudentId.textContent = studentId;
                if (modalCourseCode) modalCourseCode.textContent = courseFull;
                if (modalCurrentGrade) {
                    modalCurrentGrade.textContent = (currentGrade && currentGrade.toUpperCase() !== "N/A" && currentGrade.trim() !== "") ? currentGrade : "Not yet graded.";
                }
                if (newGradeInput) newGradeInput.value = '';
                if (gradeValidationError) gradeValidationError.textContent = ''; // Clear previous errors
                showModal(changeGradeModal);
            }
        });
    }

    // Change Grade Modal (First Step) - Close/Cancel
    [cancelChangeGradeBtn, changeGradeModalCloseBtn].forEach(btn => {
        if (btn) btn.addEventListener('click', () => {
            hideModal(changeGradeModal);
            if (gradeValidationError) gradeValidationError.textContent = ''; // Clear errors on close
        });
    });
    if (changeGradeModal) changeGradeModal.addEventListener('click', e => {
        if (e.target === changeGradeModal) {
            hideModal(changeGradeModal);
            if (gradeValidationError) gradeValidationError.textContent = ''; // Clear errors on close
        }
    });

    // Change Grade Modal (First Step) - "Proceed to Confirm"
    if (confirmChangeGradeBtn) {
        confirmChangeGradeBtn.addEventListener('click', () => {
            if (!currentChangeGradeData || !newGradeInput) return;

            const newGradeValue = newGradeInput.value.trim().toUpperCase();

            // Validate if empty
            if (!newGradeValue) {
                if (gradeValidationError) gradeValidationError.textContent = "New Grade cannot be empty.";
                newGradeInput.focus();
                return;
            }

            // Validate against accepted grades list
            if (!ACCEPTED_GRADES_SET.has(newGradeValue)) {
                if (gradeValidationError) {
                    gradeValidationError.textContent = `Invalid input, accepted inputs - ${ACCEPTED_GRADES_STRING}`;
                }
                newGradeInput.focus();
                return;
            }

            // If all validations pass
            if (gradeValidationError) gradeValidationError.textContent = ''; // Clear any previous error
            currentChangeGradeData.newGrade = newGradeValue;

            // Populate and show the final confirmation modal
            if (finalConfirmGradeMessage) {
                let message = `Are you sure you want to change the grade for ${currentChangeGradeData.studentFullName} (${currentChangeGradeData.studentId}) in course ${currentChangeGradeData.courseCode} `;
                message += (currentChangeGradeData.currentGrade && currentChangeGradeData.currentGrade.toUpperCase() !== "N/A" && currentChangeGradeData.currentGrade.trim() !== "") ?
                    `from "${currentChangeGradeData.currentGrade}" to "${currentChangeGradeData.newGrade}"?` :
                    `to "${currentChangeGradeData.newGrade}"? (No previous grade was recorded).`;
                finalConfirmGradeMessage.textContent = message;
            }
            hideModal(changeGradeModal);
            showModal(finalConfirmGradeModal);
        });
    }

    // Final Confirmation Modal - Close/Cancel ("Go Back")
    if (cancelFinalSaveBtn) {
        cancelFinalSaveBtn.addEventListener('click', () => {
            hideModal(finalConfirmGradeModal);
            showModal(changeGradeModal); // Re-open the first modal to allow edits
            if (newGradeInput) newGradeInput.focus();
            // Don't clear gradeValidationError here, user might want to see it again or it was already handled
        });
    }
    if (finalConfirmModalCloseBtn) finalConfirmModalCloseBtn.addEventListener('click', () => {
        hideModal(finalConfirmGradeModal);
        currentChangeGradeData = null;
    });
    if (finalConfirmGradeModal) finalConfirmGradeModal.addEventListener('click', e => {
        if (e.target === finalConfirmGradeModal) {
            hideModal(finalConfirmGradeModal);
            currentChangeGradeData = null;
        }
    });

    // Final Confirmation Modal - "Confirm & Save Grade"
    if (confirmFinalSaveBtn) {
        confirmFinalSaveBtn.addEventListener('click', () => {
            if (!currentChangeGradeData || !currentChangeGradeData.newGrade) {
                console.error("No data to confirm save.");
                hideModal(finalConfirmGradeModal);
                return;
            }
            console.log(`FINAL SAVE: Student ID: ${currentChangeGradeData.studentId}, Course: ${currentChangeGradeData.courseCode}, New Grade: ${currentChangeGradeData.newGrade}`);
            confirmFinalSaveBtn.disabled = true;
            confirmFinalSaveBtn.textContent = "Saving...";

            // Simulate API call
            setTimeout(() => {
                // Update table UI
                const rows = tableBody.getElementsByTagName('tr');
                for (let row of rows) {
                    if (row.dataset.studentId === currentChangeGradeData.studentId &&
                        row.dataset.course && row.dataset.course.startsWith(currentChangeGradeData.courseCode)) {
                        const gradeCell = row.cells[3];
                        if (gradeCell) gradeCell.textContent = currentChangeGradeData.newGrade;
                        row.dataset.currentGrade = currentChangeGradeData.newGrade;
                        const changeButton = row.querySelector('.change-grade-btn');
                        if (changeButton) {
                            changeButton.dataset.currentGrade = currentChangeGradeData.newGrade;
                            updateChangeGradeButtonState(changeButton, currentChangeGradeData.newGrade);
                        }
                        break;
                    }
                }

                hideModal(finalConfirmGradeModal);
                confirmFinalSaveBtn.disabled = false;
                confirmFinalSaveBtn.textContent = "Confirm & Save Grade";

                if (successModalMessage) {
                    successModalMessage.textContent = `Grade for ${currentChangeGradeData.studentFullName} (${currentChangeGradeData.studentId}) in ${currentChangeGradeData.courseCode} successfully changed to ${currentChangeGradeData.newGrade}.`;
                }
                showModal(successModal);

                currentChangeGradeData = null;
            }, 1000);
        });
    }

    // Event listeners for Success Modal
    if (successModalOkBtn) {
        successModalOkBtn.addEventListener('click', () => hideModal(successModal));
    }
    if (successModalCloseBtn) {
        successModalCloseBtn.addEventListener('click', () => hideModal(successModal));
    }
    if (successModal) {
        successModal.addEventListener('click', (event) => {
            if (event.target === successModal) {
                hideModal(successModal);
            }
        });
    }

    console.log("allST.js: Initialized and event listeners set up.");
});