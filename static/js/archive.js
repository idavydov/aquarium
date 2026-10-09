/* The archive remains readable and navigable without this enhancement. */
(() => {
  'use strict';
  const params = new URLSearchParams(location.search);
  const debug = params.get('debug') === '1';
  const strips = debug && params.get('view') === 'strips';
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
    if (debug) url.searchParams.set('debug', '1');
    if (strips) url.searchParams.set('view', 'strips');
    if (strips && params.has('width')) url.searchParams.set('width', params.get('width'));
    link.href = url.pathname + url.search + url.hash;
  };

  if (form) {
    const input = document.getElementById('search-query');
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

  document.querySelectorAll('a[href="/"], [data-search-link], [data-debug-prev], [data-debug-next]').forEach(link => decorateLink(link, query));
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

  // Debug shortcuts deliberately do not exist outside ?debug=1.
  if (debug) {
    let stripTrack = null;
    const toggle = document.getElementById('debug-strip-toggle');
    if (toggle) {
      const url = new URL(location.href);
      url.searchParams.set('debug', '1');
      if (strips) url.searchParams.delete('view');
      else url.searchParams.set('view', 'strips');
      toggle.href = url.pathname + url.search;
      toggle.textContent = strips ? 'Обычный вид' : 'Мобильная лента';
      document.getElementById('debug-view-controls').hidden = false;
    }
    const navigation = document.getElementById('debug-navigation');
    if (navigation) {
      navigation.hidden = false;
      const exit = document.getElementById('debug-exit');
      const url = new URL(location.href);
      url.searchParams.delete('debug');
      url.searchParams.delete('view');
      url.searchParams.delete('width');
      exit.href = url.pathname + url.search;
    }
    const shortcuts = event => {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey
          || event.target.closest('input, textarea, select, button, [contenteditable]:not([contenteditable="false"])')) return;
      const key = event.key.toLowerCase();
      if (key === 'h' || key === 'arrowleft' || key === 'l' || key === 'arrowright') {
        const link = document.querySelector(key === 'h' || key === 'arrowleft' ? '[data-debug-prev]' : '[data-debug-next]');
        if (link) { event.preventDefault(); location.assign(link.href); }
      } else if (['j', 'k', 'arrowdown', 'arrowup', 'pagedown', 'pageup'].includes(key)) {
        event.preventDefault();
        const direction = ['j', 'arrowdown', 'pagedown'].includes(key) ? 1 : -1;
        if (stripTrack) stripTrack.scrollBy({left: direction * (stripTrack.clientWidth - 32), behavior: 'instant'});
        else window.scrollBy({top: direction * Math.round(innerHeight * .85), behavior: 'instant'});
      }
    };
    document.addEventListener('keydown', shortcuts);

    if (strips && toggle) {
      // Real mobile-width documents, cut at exact pixel offsets. CSS columns
      // would reflow the page and could hide the mobile layout being inspected.
      const viewer = document.createElement('section');
      viewer.className = 'debug-strip-view';
      viewer.setAttribute('aria-label', 'Мобильная лента проверки');
      const toolbar = document.createElement('div');
      toolbar.className = 'debug-strip-toolbar';
      const title = document.createElement('strong');
      title.textContent = document.querySelector('h1').textContent;
      toolbar.append(title, toggle);
      document.querySelectorAll('[data-debug-prev], [data-debug-next], #debug-exit').forEach(link => {
        const copy = link.cloneNode(true);
        if (link.hasAttribute('data-debug-prev')) copy.textContent = '← Предыдущая';
        if (link.hasAttribute('data-debug-next')) copy.textContent = 'Следующая →';
        toolbar.append(copy);
      });
      const widthLabel = document.createElement('label');
      widthLabel.textContent = 'Ширина: ';
      const widths = document.createElement('select');
      [320, 360, 390, 430].forEach(width => widths.add(new Option(`${width} px`, width)));
      widths.value = params.get('width') || '390';
      if (!widths.value) widths.value = '390';
      widthLabel.append(widths);
      const status = document.createElement('span');
      status.setAttribute('role', 'status');
      toolbar.append(widthLabel, status);
      stripTrack = document.createElement('div');
      stripTrack.className = 'debug-strip-track';
      viewer.append(toolbar, stripTrack);
      document.body.append(viewer);
      document.body.classList.add('debug-strips');
      document.querySelector('main').hidden = true;
      document.getElementById('debug-view-controls').hidden = true;
      let generation = 0;
      const buildStrips = () => {
        const current = ++generation;
        const width = Number(widths.value);
        const height = Math.max(120, stripTrack.clientHeight - 40);
        stripTrack.replaceChildren();
        status.textContent = 'Загрузка…';
        const url = new URL(location.href);
        ['debug', 'view', 'width'].forEach(name => url.searchParams.delete(name));
        const addSlice = index => {
          const slice = document.createElement('div');
          slice.className = 'debug-strip-slice';
          const label = document.createElement('div');
          label.className = 'debug-strip-label';
          label.textContent = `${index + 1} · ${width} × ${height}`;
          const frame = document.createElement('iframe');
          frame.width = width;
          frame.height = height;
          frame.title = `Часть ${index + 1}: ${title.textContent}`;
          frame.addEventListener('load', () => {
            if (current !== generation) return;
            const doc = frame.contentDocument;
            const pageHeight = doc.documentElement.scrollHeight;
            // Extra space lets the last slice start at its exact offset too.
            doc.body.style.paddingBottom = `${height}px`;
            doc.documentElement.style.overflow = 'hidden';
            frame.contentWindow.scrollTo(0, index * height);
            doc.addEventListener('keydown', shortcuts);
            doc.addEventListener('click', event => {
              const link = event.target.closest('a');
              if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && event.button === 0) {
                const target = new URL(link.href);
                if (target.origin === location.origin) {
                  event.preventDefault();
                  target.searchParams.set('debug', '1');
                  target.searchParams.set('view', 'strips');
                  target.searchParams.set('width', widths.value);
                  location.assign(target.href);
                }
              } else if (event.target.closest('#font-smaller, #font-larger')) {
                // Text size changes pagination; rebuild every slice together.
                buildStrips();
              }
            });
            doc.addEventListener('wheel', event => {
              // Keep horizontal tab scrolling inside its own music block.
              if (Math.abs(event.deltaY) > Math.abs(event.deltaX) && !event.shiftKey) {
                event.preventDefault();
                stripTrack.scrollBy({left: event.deltaY, behavior: 'instant'});
              }
            }, {passive: false});
            if (!index) {
              const count = Math.ceil(pageHeight / height);
              status.textContent = `Полос: ${count} · j/k: прокрутка ленты`;
              for (let next = 1; next < count; next++) addSlice(next);
            }
          });
          frame.src = url.pathname + url.search;
          slice.append(label, frame);
          stripTrack.append(slice);
        };
        addSlice(0);
      };
      widths.addEventListener('change', () => {
        const url = new URL(location.href);
        url.searchParams.set('width', widths.value);
        history.replaceState(null, '', url.pathname + url.search);
        document.querySelectorAll('[data-debug-prev], [data-debug-next]').forEach(link => {
          const target = new URL(link.href);
          target.searchParams.set('width', widths.value);
          link.href = target.pathname + target.search;
        });
        buildStrips();
      });
      let resizeTimer;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(buildStrips, 150);
      });
      buildStrips();
    }
  }
})();
