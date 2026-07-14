/**
 * theme.js — Dark / Light mode toggle for OptiCrop AI.
 *
 * Persistence : localStorage key 'opticrop-theme' ('light' | 'dark').
 * Mechanism   : Sets data-bs-theme on the <html> element, which Bootstrap 5
 *               uses natively to switch all component colours.  DO NOT use
 *               body.style overrides — those bypass Bootstrap's theming.
 */

(function () {
  const STORAGE_KEY = 'opticrop-theme';
  const root = document.documentElement;

  /** Apply a theme without touching inline styles. */
  function applyTheme(theme) {
    root.setAttribute('data-bs-theme', theme);
    const icon = document.getElementById('theme-icon');
    if (icon) {
      icon.textContent = theme === 'dark' ? 'light_mode' : 'dark_mode';
    }
  }

  /** Read the stored preference; default to 'light'. */
  function getSavedTheme() {
    return localStorage.getItem(STORAGE_KEY) || 'light';
  }

  // Apply theme immediately (before DOMContentLoaded) to prevent flash.
  applyTheme(getSavedTheme());

  /** Public toggle called by the navbar button. */
  window.toggleTheme = function () {
    const next = getSavedTheme() === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  };

  document.addEventListener('DOMContentLoaded', () => {
    // Re-apply in case the DOM wasn't ready for the icon swap above.
    applyTheme(getSavedTheme());

    // Animate fade-in-up elements.
    document.querySelectorAll('.fade-in-up, .fade-up').forEach((el, i) => {
      setTimeout(() => el.classList.add('visible'), 80 * i);
    });
  });
})();

/** CSRF token helper — used by fetch() calls in templates. */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}
