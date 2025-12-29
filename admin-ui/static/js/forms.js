/**
 * Form handling for route subscription forms
 */

console.log('[forms.js] Script loading...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('[forms.js] DOMContentLoaded event fired');
    
    // Handle route form
    const routeForm = document.getElementById('routeForm');
    console.log('[forms.js] Route form found:', !!routeForm);
    if (routeForm) {
        routeForm.addEventListener('submit', handleRouteFormSubmit);
        console.log('[forms.js] Route form submit listener attached');
    }
    
    // Handle source form
    const sourceForm = document.getElementById('sourceForm');
    console.log('[forms.js] Source form found:', !!sourceForm);
    if (sourceForm) {
        sourceForm.addEventListener('submit', handleSourceFormSubmit);
        console.log('[forms.js] Source form submit listener attached');
        
        // Pre-fill form if in edit mode
        if (typeof sourceData !== 'undefined' && sourceData) {
            if (sourceData.country) {
                const countrySelect = document.getElementById('country');
                if (countrySelect) {
                    // Wait for countries to be populated
                    setTimeout(() => {
                        countrySelect.value = sourceData.country;
                    }, 100);
                }
            }
            if (sourceData.visa_type) {
                document.getElementById('visa_type').value = sourceData.visa_type;
            }
            if (sourceData.fetch_type) {
                document.getElementById('fetch_type').value = sourceData.fetch_type;
            }
            if (sourceData.check_frequency) {
                document.getElementById('check_frequency').value = sourceData.check_frequency;
            }
        }
    }
});

/**
 * Handle route form submission
 */
async function handleRouteFormSubmit(e) {
    console.log('[forms.js] handleRouteFormSubmit called');
    try {
        const form = e.target;
        e.preventDefault();
        console.log('[forms.js] Form submission prevented');
        
        // Hide previous messages
        hideMessages();
        console.log('[forms.js] Messages hidden');
        
        // Clear previous field errors
        clearFieldErrors();
        console.log('[forms.js] Field errors cleared');
    
    // Collect form data
    const formData = {
        origin_country: document.getElementById('origin_country').value,
        destination_country: document.getElementById('destination_country').value,
        visa_type: document.getElementById('visa_type').value,
        email: document.getElementById('email').value,
        is_active: document.getElementById('is_active').checked
    };
    
        // Client-side validation
        console.log('[forms.js] Validating route form data:', formData);
        if (!validateRouteForm(formData)) {
            console.log('[forms.js] Route form validation failed');
            return;
        }
        console.log('[forms.js] Route form validation passed');
        
        // Disable submit button
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Saving...';
        console.log('[forms.js] Submit button disabled');
        
        try {
            const routeId = document.getElementById('routeId').value;
            let result;
            
            if (routeId) {
                // Update existing route
                result = await API.updateRoute(routeId, formData);
            } else {
                // Create new route
                result = await API.createRoute(formData);
            }
            
            // Show success message
            console.log('[forms.js] Route saved successfully');
            showSuccessMessage();
            
            // Redirect to routes list after a short delay
            setTimeout(() => {
                console.log('[forms.js] Redirecting to /routes');
                window.location.href = '/routes';
            }, 1500);
            
        } catch (error) {
            console.error('[forms.js] Error in handleRouteFormSubmit:', error);
            // Parse error message from API response
            let errorMessage = error.message;
        try {
            // Try to extract more detailed error from response
            if (error.response) {
                const errorData = await error.response.json().catch(() => null);
                if (errorData?.detail) {
                    if (typeof errorData.detail === 'string') {
                        errorMessage = errorData.detail;
                    } else if (errorData.detail.message) {
                        errorMessage = errorData.detail.message;
                    } else if (errorData.detail.details) {
                        errorMessage = JSON.stringify(errorData.detail.details);
                    }
                }
            }
        } catch (e) {
            // Use original error message if parsing fails
        }
        
        // Show error message
        showErrorMessage(errorMessage);
        
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = originalText;
        }
    } catch (error) {
        console.error('[forms.js] Fatal error in handleRouteFormSubmit:', error);
        console.error('[forms.js] Error stack:', error.stack);
    }
}

/**
 * Handle source form submission
 */
async function handleSourceFormSubmit(e) {
    console.log('[forms.js] handleSourceFormSubmit called');
    try {
        const form = e.target;
        e.preventDefault();
        console.log('[forms.js] Form submission prevented');
        
        // Hide previous messages
        hideMessages();
        console.log('[forms.js] Messages hidden');
        
        // Clear previous field errors
        clearFieldErrors();
        console.log('[forms.js] Field errors cleared');
    
    // Collect form data
    const formData = {
        country: document.getElementById('country').value,
        visa_type: document.getElementById('visa_type').value,
        url: document.getElementById('url').value,
        name: document.getElementById('name').value,
        fetch_type: document.getElementById('fetch_type').value,
        check_frequency: document.getElementById('check_frequency').value,
        is_active: document.getElementById('is_active').checked
    };
    
        // Client-side validation
        console.log('[forms.js] Validating source form data:', formData);
        if (!validateSourceForm(formData)) {
            console.log('[forms.js] Source form validation failed');
            return;
        }
        console.log('[forms.js] Source form validation passed');
        
        // Disable submit button
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Saving...';
        console.log('[forms.js] Submit button disabled');
        
        try {
            const sourceId = document.getElementById('sourceId').value;
            let result;
            
            if (sourceId) {
                // Update existing source
                result = await API.updateSource(sourceId, formData);
            } else {
                // Create new source
                result = await API.createSource(formData);
            }
            
            // Show success message
            console.log('[forms.js] Source saved successfully');
            showSuccessMessage();
            
            // Redirect to sources list after a short delay
            setTimeout(() => {
                console.log('[forms.js] Redirecting to /sources');
                window.location.href = '/sources';
            }, 1500);
            
        } catch (error) {
            console.error('[forms.js] Error in handleSourceFormSubmit:', error);
            // Parse error message from API response
            let errorMessage = error.message;
        try {
            // Try to extract more detailed error from response
            if (error.response) {
                const errorData = await error.response.json().catch(() => null);
                if (errorData?.detail) {
                    if (typeof errorData.detail === 'string') {
                        errorMessage = errorData.detail;
                    } else if (errorData.detail.message) {
                        errorMessage = errorData.detail.message;
                    } else if (errorData.detail.details) {
                        errorMessage = JSON.stringify(errorData.detail.details);
                    }
                }
            }
        } catch (e) {
            // Use original error message if parsing fails
        }
        
        // Show error message
        showErrorMessage(errorMessage);
        
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = originalText;
        }
    } catch (error) {
        console.error('[forms.js] Fatal error in handleSourceFormSubmit:', error);
        console.error('[forms.js] Error stack:', error.stack);
    }
}

/**
 * Validate route form data
 */
function validateRouteForm(data) {
    console.log('[forms.js] validateRouteForm called with:', data);
    let isValid = true;
    
    // Validate origin country
    if (!data.origin_country || data.origin_country.length !== 2) {
        showFieldError('origin_country', 'Origin country is required');
        isValid = false;
    }
    
    // Validate destination country
    if (!data.destination_country || data.destination_country.length !== 2) {
        showFieldError('destination_country', 'Destination country is required');
        isValid = false;
    }
    
    // Validate visa type
    if (!data.visa_type) {
        showFieldError('visa_type', 'Visa type is required');
        isValid = false;
    }
    
    // Validate email
    if (!data.email) {
        showFieldError('email', 'Email is required');
        isValid = false;
    } else if (!isValidEmail(data.email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate source form data
 */
function validateSourceForm(data) {
    console.log('[forms.js] validateSourceForm called with:', data);
    let isValid = true;
    
    // Validate country
    if (!data.country || data.country.length !== 2) {
        showFieldError('country', 'Country is required (2 character code)');
        isValid = false;
    }
    
    // Validate visa type
    if (!data.visa_type) {
        showFieldError('visa_type', 'Visa type is required');
        isValid = false;
    }
    
    // Validate URL
    if (!data.url) {
        showFieldError('url', 'URL is required');
        isValid = false;
    } else if (!isValidUrl(data.url)) {
        showFieldError('url', 'Please enter a valid URL (must start with http:// or https://)');
        isValid = false;
    }
    
    // Validate name
    if (!data.name || data.name.trim().length === 0) {
        showFieldError('name', 'Name is required');
        isValid = false;
    }
    
    // Validate fetch type
    if (!data.fetch_type) {
        showFieldError('fetch_type', 'Fetch type is required');
        isValid = false;
    } else if (!['html', 'pdf'].includes(data.fetch_type)) {
        showFieldError('fetch_type', 'Fetch type must be HTML or PDF');
        isValid = false;
    }
    
    // Validate check frequency
    if (!data.check_frequency) {
        showFieldError('check_frequency', 'Check frequency is required');
        isValid = false;
    }
    
    return isValid;
}

/**
 * Validate URL format
 */
function isValidUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch (e) {
        return false;
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Show field error
 */
function showFieldError(fieldName, message) {
    const field = document.getElementById(fieldName);
    const errorElement = document.getElementById(`${fieldName}_error`);
    
    if (field) {
        field.classList.add('border-red-500');
    }
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
}

/**
 * Clear all field errors
 */
function clearFieldErrors() {
    const errorElements = document.querySelectorAll('[id$="_error"]');
    errorElements.forEach(el => {
        el.classList.add('hidden');
        el.textContent = '';
    });
    
    const fields = document.querySelectorAll('input, select');
    fields.forEach(field => {
        field.classList.remove('border-red-500');
    });
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Show success message
 */
function showSuccessMessage() {
    const successDiv = document.getElementById('successMessage');
    if (successDiv) {
        successDiv.classList.remove('hidden');
        successDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

/**
 * Hide all messages
 */
function hideMessages() {
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    if (errorDiv) errorDiv.classList.add('hidden');
    if (successDiv) successDiv.classList.add('hidden');
}

