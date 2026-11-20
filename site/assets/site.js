// ReviewReplay site: tabs, copy buttons, case filter, video dialog, reveal on scroll.
(function () {
  'use strict';
  document.documentElement.classList.remove('no-js');

  // The embedded Archify pages read these keys (same origin). Start them light and live,
  // unless the reader already chose otherwise in one of them.
  try {
    if (!localStorage.getItem('archify-theme')) localStorage.setItem('archify-theme', 'light');
    if (!localStorage.getItem('archify-motion')) localStorage.setItem('archify-motion', 'live');
  } catch (e) { /* storage blocked: the pages fall back to their own defaults */ }

  // Nav border once scrolled
  var nav = document.querySelector('.nav');
  var onScroll = function () { if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 8); };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Generic tab groups: [role=tablist] with [role=tab][aria-controls]
  function loadFrame(panel) {
    var frame = panel && panel.querySelector('iframe[data-src]');
    if (frame && !frame.getAttribute('src')) frame.setAttribute('src', frame.getAttribute('data-src'));
  }
  document.querySelectorAll('[role="tablist"]').forEach(function (list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) { panel.hidden = !on; if (on) loadFrame(panel); }
      });
      var open = list.getAttribute('data-open-link');
      if (open) {
        var link = document.getElementById(open);
        if (link && tab.dataset.href) link.href = tab.dataset.href;
      }
      if (focus) tab.focus();
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (e) {
        var next = null;
        if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === 'Home') next = tabs[0];
        if (e.key === 'End') next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next, true); }
      });
    });
    var first = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
    if (first) select(first);
  });

  // A cover over each embedded diagram, so page scrolling isn't captured by the iframe
  // until the reader clicks to explore. It comes back when the pointer leaves the frame.
  var body = document.querySelector('.frame__body');
  if (body) {
    document.querySelectorAll('.frame__panel').forEach(function (panel) {
      var shield = document.createElement('button');
      shield.type = 'button';
      shield.className = 'frame__shield';
      shield.innerHTML = '<span>Click to explore the diagram</span>';
      shield.addEventListener('click', function () {
        body.classList.add('is-exploring');
        var frame = panel.querySelector('iframe');
        if (frame) frame.focus();
      });
      panel.appendChild(shield);
    });
    body.addEventListener('mouseleave', function () { body.classList.remove('is-exploring'); });
  }

  // Links that jump to the tour and open one of its tabs
  document.querySelectorAll('[data-show-tab]').forEach(function (a) {
    a.addEventListener('click', function () {
      var tab = document.getElementById(a.getAttribute('data-show-tab'));
      if (tab) tab.click();
    });
  });

  // Copy buttons: data-copy="text" or data-copy-from="#id"
  document.querySelectorAll('[data-copy], [data-copy-from]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      if (!text) {
        var src = document.querySelector(btn.getAttribute('data-copy-from'));
        text = src ? src.innerText.replace(/^\$ /gm, '').trim() : '';
      }
      var label = btn.querySelector('.copy__label');
      var done = function () {
        btn.classList.add('is-done');
        if (label) label.textContent = 'Copied';
        setTimeout(function () { btn.classList.remove('is-done'); if (label) label.textContent = 'Copy'; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      }
    });
  });

  // Case filter
  var filters = document.querySelectorAll('.filter');
  filters.forEach(function (f) {
    f.addEventListener('click', function () {
      var want = f.getAttribute('data-filter');
      filters.forEach(function (g) { g.setAttribute('aria-pressed', g === f ? 'true' : 'false'); });
      document.querySelectorAll('.case').forEach(function (c) {
        var tags = (c.getAttribute('data-tags') || '').split(' ');
        c.hidden = !(want === 'all' || tags.indexOf(want) !== -1);
      });
      var count = document.getElementById('case-count');
      if (count) count.textContent = document.querySelectorAll('.case:not([hidden])').length;
    });
  });

  // Demo video dialog
  var dialog = document.getElementById('demo');
  if (dialog && typeof dialog.showModal === 'function') {
    var video = dialog.querySelector('video');
    document.querySelectorAll('[data-open-demo]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (video && !video.getAttribute('src')) video.setAttribute('src', video.getAttribute('data-src'));
        dialog.showModal();
        if (video) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
      });
    });
    var close = function () { if (video) video.pause(); dialog.close(); };
    dialog.querySelector('.dialog__close').addEventListener('click', close);
    dialog.addEventListener('click', function (e) { if (e.target === dialog) close(); });
    dialog.addEventListener('close', function () { if (video) video.pause(); });
  }

  // Reveal on scroll
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('is-in'); });
  }
})();
