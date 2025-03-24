async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorAlert = document.getElementById('errorAlert');
    
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            window.location.href = data.redirect || '/admin';
        } else {
            errorAlert.textContent = data.error || 'Login failed. Please try again.';
            errorAlert.style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        errorAlert.textContent = 'An error occurred. Please try again.';
        errorAlert.style.display = 'block';
    }
}

// Update field value
async function updateField(field, newValue) {
    const section = field.dataset.section;
    const key = field.dataset.key;
    const parentKey = field.dataset.parentKey;
    
    try {
        const response = await fetch('/admin/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                section: section,
                key: key,
                parent_key: parentKey,
                value: newValue
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Success', 'Value updated successfully', 'success');
            field.textContent = newValue;
            field.classList.remove('editing');
        } else {
            showToast('Error', data.error || 'Failed to update value', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error', 'An error occurred while updating the value', 'error');
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
