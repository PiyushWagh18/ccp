/**
 * CloudTask Manager - Client-side JavaScript
 * Handles form validation and UI interactions.
 */

document.addEventListener("DOMContentLoaded", function () {

    // Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const closeBtn = alert.querySelector(".btn-close");
            if (closeBtn) {
                closeBtn.click();
            }
        }, 5000);
    });

    // File size validation (16 MB maximum)
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function (input) {
        input.addEventListener("change", function () {
            const maxSize = 16 * 1024 * 1024; // 16 MB
            if (this.files.length > 0 && this.files[0].size > maxSize) {
                window.alert("File size exceeds 16 MB limit. Please choose a smaller file.");
                this.value = "";
            }
        });
    });

    // Form submission loading state
    const forms = document.querySelectorAll("form");
    forms.forEach(function (form) {
        form.addEventListener("submit", function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.getAttribute("data-no-loading")) {
                submitBtn.disabled = true;
                submitBtn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-1"></span>Processing...';
            }
        });
    });

    // Character counter for description textarea
    const descriptionField = document.getElementById("description");
    if (descriptionField) {
        const maxLength = parseInt(descriptionField.getAttribute("maxlength")) || 2000;
        const counter = document.createElement("div");
        counter.className = "form-text text-end";
        counter.textContent = "0 / " + maxLength + " characters";
        descriptionField.parentNode.appendChild(counter);

        descriptionField.addEventListener("input", function () {
            counter.textContent = this.value.length + " / " + maxLength + " characters";
        });

        // Update counter on page load for edit forms
        counter.textContent =
            descriptionField.value.length + " / " + maxLength + " characters";
    }
});
