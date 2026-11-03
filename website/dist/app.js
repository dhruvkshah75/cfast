/* The website is static. Demo buttons never execute visitor code. */
(() => {
  'use strict';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];
  const motionToggle = $('#motion-toggle');
  let motionPaused = false;
  function syncMotion() {
    const pause = reducedMotion.matches || motionPaused;
    document.documentElement.classList.toggle('motion-paused', pause);
    if (motionToggle) {
      motionToggle.hidden = reducedMotion.matches;
      motionToggle.setAttribute('aria-pressed', String(motionPaused));
      motionToggle.textContent = motionPaused ? 'Resume motion' : 'Pause motion';
    }
    if (pause) $$('.word').forEach(word => word.classList.add('is-active'));
  }
  motionToggle?.addEventListener('click', () => {
    motionPaused = !motionPaused;
    syncMotion();
  });
  reducedMotion.addEventListener('change', syncMotion);
  syncMotion();
  const toast = $('#toast');
  let toastTimer;
  function notify(message) {
    if (!toast) return;
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add('is-visible');
    toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 4500);
  }

  // Keyboard navigation follows the ARIA tabs pattern.
  function setupTabs(selector, onSelect) {
    const tabs = $$(selector);
    function select(tab, moveFocus = false) {
      tabs.forEach(item => {
        const active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
      });
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      panel?.setAttribute('aria-labelledby', tab.id);
      if (moveFocus) tab.focus();
      onSelect(tab);
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== undefined) {
          event.preventDefault();
          select(tabs[next], true);
        }
      });
    });
  }

  const demoLines = $('#demo-lines');
  let demoGeneration = 0;
  let selectedDemo = 'pass';
  const common = [
    ['term-muted', 'problem 4A: 4A.cpp'],
    ['term-muted', 'limits: 2s CPU, 256 MiB address space'],
    ['term-muted term-compile', 'compiling 4A.cpp ...']
  ];
  const demos = {
    pass: [...common,
      ['term-green', 'test 1: OK'],
      ['term-muted term-metric', '0.000s CPU · 0.004s wall · 3.12 MiB peak RSS'],
      ['term-output', '--got--\nYES\n--expected--\nYES'],
      ['term-green term-summary', 'PASSED: 1/1 passed']],
    wa: [...common,
      ['term-red', 'test 1: WA'],
      ['term-muted term-metric', '0.000s CPU · 0.005s wall · 3.14 MiB peak RSS'],
      ['term-output', '--input--\n8\n--got--\nNO\n--expected--\nYES'],
      ['term-red term-summary', 'FAILED: 0/1 passed (1 failed)']],
    tle: [...common,
      ['term-red', 'test 1: TLE'],
      ['term-muted term-metric', '2.000s CPU · 2.013s wall · 3.12 MiB peak RSS'],
      ['term-detail', 'The CPU time limit was exceeded.'],
      ['term-red term-summary', 'FAILED: 0/1 passed (1 failed)']]
  };
  function renderDemo(kind, animate = true) {
    if (!demoLines) return;
    const generation = ++demoGeneration;
    selectedDemo = kind;
    demoLines.replaceChildren();
    demos[kind].forEach(([className, value], index) => {
      const append = () => {
        if (generation !== demoGeneration) return;
        const p = document.createElement('p');
        p.className = className + (animate && !reducedMotion.matches && !motionPaused ? ' demo-line' : '');
        p.style.whiteSpace = 'pre-line';
        p.textContent = value;
        demoLines.append(p);
      };
      if (animate && !reducedMotion.matches && !motionPaused) setTimeout(append, index * 110);
      else append();
    });
  }
  setupTabs('.demo-tab', tab => renderDemo(tab.dataset.demo));
  $('#replay-demo')?.addEventListener('click', () => renderDemo(selectedDemo));

  const commandData = {
    run: [
      ['cfast 4A', 'Compile and check every saved case.'],
      ['cfast 4A --timeout 2 --memory 256', 'Override CPU seconds and memory in MiB.'],
      ['cfast 4A --eps 1e-6', 'Set an explicit floating point tolerance.'],
      ['cfast --help', 'See every command, grouped by purpose.']
    ],
    add: [
      ['cfast add 4A', 'Open an editor to add input and expected output.'],
      ['cfast add 4A --input input.txt --output expected.txt', 'Import a custom case from two files.'],
      ["EDITOR='subl -w' cfast add 4A", 'Wait for edits in Sublime Text before saving the case.'],
      ['', 'Custom cases are kept when you import the problem again.']
    ],
    clean: [
      ['cfast clean', 'Preview downloaded samples unused for 30 days.'],
      ['cfast clean --yes', 'Remove the downloads shown in that preview.'],
      ['cfast clean --all --samples-only --yes', 'Remove all downloads, keeping custom cases.'],
      ['cfast clean --all --yes', 'Full reset: deletes downloaded AND custom cases.']
    ]
  };
  setupTabs('.command-tab', tab => {
    const panel = $('#command-panel');
    panel.replaceChildren();
    commandData[tab.dataset.command].forEach(([command, description], index) => {
      const row = document.createElement('div');
      row.className = 'command-entry';
      if (command) {
        const code = document.createElement('code');
        code.textContent = command;
        row.append(code);
      }
      const p = document.createElement('p');
      p.className = 'body-6';
      p.textContent = description;
      if (tab.dataset.command === 'clean' && index === 3) row.classList.add('command-warning');
      row.append(p);
      panel.append(row);
    });
  });

  $$('.copy-button').forEach(button => {
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.copy);
      if (!target) return;
      const label = button.querySelector('span');
      button.disabled = true;
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(target.textContent.trim());
        label.textContent = 'Copied';
        button.querySelector('use').setAttribute('href', '#i-check');
        notify('Commands copied. Paste them into your terminal.');
      } catch {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        label.textContent = 'Selected';
        notify('Clipboard unavailable. Commands selected; press Ctrl+C or copy manually.');
      } finally {
        button.disabled = false;
        setTimeout(() => {
          label.textContent = 'Copy';
          button.querySelector('use').setAttribute('href', '#i-copy');
        }, 3500);
      }
    });
  });

  const menuToggle = $('.menu-toggle');
  const menu = $('#mobile-menu');
  function closeMenu(restoreFocus = false) {
    if (!menu) return;
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open navigation');
    menu.classList.remove('is-open');
    menu.hidden = true;
    menu.inert = true;
    document.body.classList.remove('menu-open');
    $('#main').inert = false;
    $('.footer').inert = false;
    if (restoreFocus) menuToggle.focus();
  }
  menuToggle?.addEventListener('click', () => {
    if (menuToggle.getAttribute('aria-expanded') === 'true') return closeMenu(true);
    menu.hidden = false;
    menu.inert = false;
    menuToggle.setAttribute('aria-expanded', 'true');
    menuToggle.setAttribute('aria-label', 'Close navigation');
    document.body.classList.add('menu-open');
    $('#main').inert = true;
    $('.footer').inert = true;
    requestAnimationFrame(() => {
      menu.classList.add('is-open');
      menu.querySelector('a').focus();
    });
  });
  menu?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => closeMenu()));
  document.addEventListener('keydown', event => {
    if (menuToggle?.getAttribute('aria-expanded') !== 'true') return;
    if (event.key === 'Escape') closeMenu(true);
    if (event.key === 'Tab') {
      const links = [menuToggle, ...menu.querySelectorAll('a')];
      const first = links[0], last = links[links.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  window.matchMedia('(max-width: 600px)').addEventListener('change', event => {
    if (!event.matches && menuToggle?.getAttribute('aria-expanded') === 'true') closeMenu();
  });

  // Content remains visible if JavaScript or IntersectionObserver is unavailable.
  if ('IntersectionObserver' in window) {
    document.documentElement.classList.add('js');
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      });
    }, { threshold: 0.08 });
    $$('.reveal').forEach(element => revealObserver.observe(element));

    const tagline = $('.word-reveal');
    if (tagline && !reducedMotion.matches) {
      const lines = tagline.innerHTML.split(/<br\s*\/?>/i);
      tagline.replaceChildren();
      lines.forEach((line, lineIndex) => {
        if (lineIndex) tagline.append(document.createElement('br'));
        line.split(/\s+/).filter(Boolean).forEach((word, index) => {
          if (index) tagline.append(' ');
          const span = document.createElement('span');
          span.className = 'word';
          span.textContent = word;
          tagline.append(span);
        });
      });
      const words = [...tagline.querySelectorAll('.word')];
      const wordObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          const index = words.indexOf(entry.target);
          setTimeout(() => entry.target.classList.add('is-active'), index * 60);
          wordObserver.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -18% 0px', threshold: 0.5 });
      words.forEach(word => wordObserver.observe(word));
      reducedMotion.addEventListener('change', event => {
        if (event.matches) {
          words.forEach(word => word.classList.add('is-active'));
          wordObserver.disconnect();
        }
      });
    }
    const sectionObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        $$('.desktop-links a').forEach(link => {
          if (link.getAttribute('href') === '#' + entry.target.id) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-10% 0px -65% 0px' });
    $$('main > section[id]').forEach(section => sectionObserver.observe(section));
  }
})();
