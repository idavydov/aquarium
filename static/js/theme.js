/* Apply a saved preference before the stylesheet paints the next page. */
(() => {
  'use strict';
  const root = document.documentElement;
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  const storageKey = 'aquarium-theme';
  const readPreference = () => {
    try { return localStorage.getItem(storageKey); } catch (_) { return null; }
  };
  const applyPreference = preference => {
    if (preference === 'light' || preference === 'dark') root.dataset.theme = preference;
    else delete root.dataset.theme;
  };
  const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : systemTheme.matches;
  applyPreference(readPreference());

  document.addEventListener('DOMContentLoaded', () => {
    const buttons = Array.from(document.querySelectorAll('.theme-toggle'));
    const updateButtons = () => {
      const dark = isDark();
      buttons.forEach(button => {
        const label = dark ? 'Включить светлую тему' : 'Включить тёмную тему';
        button.setAttribute('aria-label', label);
        button.title = label;
        button.querySelector('[data-theme-icon="light"]').toggleAttribute('hidden', !dark);
        button.querySelector('[data-theme-icon="dark"]').toggleAttribute('hidden', dark);
        button.hidden = false;
      });
    };
    buttons.forEach(button => button.addEventListener('click', () => {
      const preference = isDark() ? 'light' : 'dark';
      applyPreference(preference);
      try { localStorage.setItem(storageKey, preference); } catch (_) {}
      updateButtons();
    }));
    systemTheme.addEventListener('change', updateButtons);
    window.addEventListener('storage', event => {
      if (event.key === storageKey || event.key === null) {
        applyPreference(readPreference());
        updateButtons();
      }
    });
    updateButtons();
  });
})();
