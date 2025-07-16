// Standardized AJAX helper function
async function makeAjaxRequest(url, data = null, method = 'GET') {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `Request failed with status ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('AJAX Request Error:', error);
        throw error;
    }
}

// Update field value
async function updateField(field, newValue) {
    const section = field.dataset.section;
    const key = field.dataset.key;
    const parentKey = field.dataset.parentKey;

    try {
        const data = await makeAjaxRequest('/admin/update', {
            section: section,
            key: key,
            parent_key: parentKey,
            value: newValue
        }, 'POST');

        showToast('Success', 'Value updated successfully', 'success');
        field.textContent = newValue;
        field.classList.remove('editing');
    } catch (error) {
        showToast('Error', error.message || 'An error occurred while updating the value', 'error');
    }
}

// Save all edits in a section
async function saveAllEdits(section) {
    const fields = document.querySelectorAll(`[data-section="${section}"].editing`);
    let success = true;

    for (const field of fields) {
        try {
            await updateField(field, field.textContent);
        } catch (error) {
            success = false;
            console.error('Error saving field:', error);
        }
    }

    if (success) {
        showToast('Success', 'All changes saved successfully', 'success');
    } else {
        showToast('Error', 'Some changes could not be saved', 'error');
    }
}

// Show toast notification
function showToast(title, message, type = 'success') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type} show`;
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;

    document.querySelector('.toast-container').appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Make fields editable on click
document.addEventListener('DOMContentLoaded', () => {
    const editableFields = document.querySelectorAll('.editable-field');

    editableFields.forEach(field => {
        field.addEventListener('click', function() {
            if (!this.classList.contains('editing')) {
                this.contentEditable = true;
                this.classList.add('editing');
                this.focus();
            }
        });

        field.addEventListener('blur', function() {
            this.contentEditable = false;
            if (this.classList.contains('editing')) {
                updateField(this, this.textContent);
            }
        });

        field.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    });
});
