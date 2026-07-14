export const FIELD_RANGES = {
    "N":           [0.0,   140.0],
    "P":           [5.0,   145.0],
    "K":           [5.0,   205.0],
    "temperature": [0.0,    50.0],
    "humidity":    [0.0,   100.0],
    "rainfall":    [0.0,   300.0],
    "ph":          [0.0,    14.0]
};

export function validateForm(form) {
    let isValid = true;
    const formData = new FormData(form);
    const data = {};
    
    // Clear previous errors
    form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    
    const fields = Object.keys(FIELD_RANGES);
    
    fields.forEach(field => {
        const valStr = formData.get(field);
        const inputEl = form.querySelector(`[name="${field}"]`);
        if (!inputEl) return;
        
        const showError = (msg) => {
            isValid = false;
            inputEl.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = msg;
            inputEl.parentNode.appendChild(errorDiv);
        };
        
        if (!valStr || valStr.trim() === '') {
            showError('Field is required.');
            return;
        }
        
        const val = parseFloat(valStr);
        if (isNaN(val)) {
            showError('Numeric value required.');
            return;
        }
        
        const [min, max] = FIELD_RANGES[field];
        if (val < min || val > max) {
            showError(`Value must be between ${min} and ${max}.`);
            return;
        }
        
        data[field] = val;
    });
    
    return { isValid, data };
}

export function bindValidationClear(form) {
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            input.classList.remove('is-invalid');
            const feedback = input.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        });
    });
}
