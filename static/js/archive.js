/* The archive remains readable and navigable without this enhancement. */
(() => {
  'use strict';
  const params = new URLSearchParams(location.search);
  const form = document.getElementById('song-search');
  const searchStorageKey = 'aquarium-search-query';
  const rememberQuery = value => {
    try { sessionStorage.setItem(searchStorageKey, value); } catch (_) {}
  };
  let query = params.get('q') || '';
  if (document.querySelector('.song-page')) {
    if (params.has('q')) rememberQuery(query);
    else {
      try { query = sessionStorage.getItem(searchStorageKey) || ''; } catch (_) {}
    }
    // Old bookmarks still work, but search state stays off the song URL.
    if (params.has('q')) {
      params.delete('q');
      const url = new URL(location.href);
      url.searchParams.delete('q');
      history.replaceState(null, '', url.pathname + url.search + url.hash);
    }
  }
  const normalize = text => text.toLocaleLowerCase('ru').replace(/ё/g, 'е').trim().replace(/\s+/g, ' ');
  const decorateLink = (link, searchQuery) => {
    const url = new URL(link.getAttribute('href'), location.href);
    if (url.origin !== location.origin) return;
    if (url.pathname === '/' && searchQuery) url.searchParams.set('q', searchQuery);
    else url.searchParams.delete('q');
    link.href = url.pathname + url.search + url.hash;
  };

  if (form) {
    const input = document.getElementById('search-query');
    const desktopSearch = window.matchMedia('(min-width: 720px)');
    const updateSearchHint = () => {
      input.placeholder = desktopSearch.matches ? 'Найти песню… (/)' : 'Найти песню…';
    };
    desktopSearch.addEventListener('change', updateSearchHint);
    updateSearchHint();
    const clear = document.getElementById('clear-search');
    const empty = document.getElementById('search-empty');
    const items = Array.from(document.querySelectorAll('#song-list li')).map(element => ({
      element, text: normalize(element.textContent), link: element.querySelector('a')
    }));
    const filter = () => {
      rememberQuery(input.value);
      const words = normalize(input.value).split(' ').filter(Boolean);
      let matches = 0;
      items.forEach(item => {
        item.element.hidden = !words.every(word => item.text.includes(word));
        if (!item.element.hidden) matches++;
        decorateLink(item.link, input.value);
      });
      empty.hidden = matches !== 0;
      clear.hidden = input.value.length === 0;
      const url = new URL(location.href);
      if (input.value) url.searchParams.set('q', input.value);
      else url.searchParams.delete('q');
      history.replaceState(null, '', url.pathname + url.search + url.hash);
    };
    input.value = query;
    input.addEventListener('input', filter);
    form.addEventListener('submit', event => event.preventDefault());
    clear.addEventListener('click', () => { input.value = ''; filter(); input.focus(); });
    window.addEventListener('pageshow', () => {
      input.value = new URLSearchParams(location.search).get('q') || '';
      filter();
    });
    filter();
    form.hidden = false;
    if (location.hash === '#search-query') {
      input.focus();
      input.select();
    }
  }

  document.querySelectorAll('a[href="/"]').forEach(link => decorateLink(link, ''));
  document.querySelectorAll('[data-search-link]').forEach(link => decorateLink(link, ''));
  document.addEventListener('keydown', event => {
    if (event.key !== '/' || event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey
        || event.target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return;
    const input = document.getElementById('search-query');
    const link = document.querySelector('[data-search-link]');
    if (!input && !link) return;
    event.preventDefault();
    if (input) { input.focus(); input.select(); }
    else location.assign(link.href);
  });
  const fontControls = document.getElementById('font-controls');
  if (fontControls) {
    let fontSize = 16;
    try {
      const saved = Number(localStorage.getItem('aquarium-font-size'));
      if (saved >= 12 && saved <= 24) fontSize = saved;
    } catch (_) { /* Storage may be disabled; controls still work. */ }
    const smaller = document.getElementById('font-smaller');
    const larger = document.getElementById('font-larger');
    const updateFont = () => {
      document.documentElement.style.setProperty('--song-font-size', `${fontSize}px`);
      fontControls.setAttribute('aria-label', `Размер текста: ${fontSize} пикселей`);
      smaller.disabled = fontSize <= 12;
      larger.disabled = fontSize >= 24;
      try { localStorage.setItem('aquarium-font-size', fontSize); } catch (_) {}
    };
    smaller.addEventListener('click', () => { fontSize = Math.max(12, fontSize - 2); updateFont(); });
    larger.addEventListener('click', () => { fontSize = Math.min(24, fontSize + 2); updateFont(); });
    updateFont();
    fontControls.hidden = false;
  }
})();
