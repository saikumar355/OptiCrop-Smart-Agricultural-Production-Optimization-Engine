export function showLoading(btn, form) {
    if (btn) {
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.setAttribute('data-original-text', originalText);
        btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...`;
    }
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.disabled = true;
        });
    }
}

export function hideLoading(btn, form) {
    if (btn) {
        btn.disabled = false;
        const originalText = btn.getAttribute('data-original-text');
        if (originalText) {
            btn.innerHTML = originalText;
        }
    }
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.disabled = false;
        });
    }
}
