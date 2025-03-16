document.addEventListener('DOMContentLoaded', function() {
    // Show modal
    function showModal(modalId) {
        const modal = document.querySelector(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    // Hide modal
    function hideModal(modal) {
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    // Update input formatting based on type
    function updateValueInput(select) {
        const isPercentage = select.value === 'percentage';
        const input = select.closest('.modal-body').querySelector('.cost-value-input');
        const suffix = select.closest('.modal-body').querySelector('.cost-type-suffix');
        
        if (input) {
            // Update step and value formatting
            input.step = isPercentage ? '0.01' : '1';
            
            // Get current value and convert it
            let currentValue = parseFloat(input.value) || 0;
            
            // Format the value based on type
            if (isPercentage) {
                input.value = currentValue.toFixed(2);
            } else {
                input.value = Math.round(currentValue);
            }
        }
        
        if (suffix) {
            suffix.textContent = isPercentage ? '%' : '$';
        }
    }

    // Handle edit buttons
    document.querySelectorAll('.edit-btn').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-bs-target');
            showModal(modalId);
        });
    });

    // Handle close buttons
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(function(button) {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            hideModal(modal);
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            hideModal(e.target);
        }
    });

    // Handle type select changes
    document.querySelectorAll('.cost-type-select').forEach(function(select) {
        // Set initial formatting
        updateValueInput(select);
        
        // Handle changes
        select.addEventListener('change', function() {
            updateValueInput(this);
        });
    });

    // Form validation
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Delete confirmation
    document.querySelectorAll('.btn-delete').forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this closing cost?')) {
                event.preventDefault();
            }
        });
    });

    // Show success toast if there's a message
    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    if (message) {
        const toastContainer = document.querySelector('.toast-container');
        const toastEl = document.createElement('div');
        toastEl.className = 'toast align-items-center text-white bg-success border-0';
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${decodeURIComponent(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }
});
