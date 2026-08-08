/**
 * SHIELD AI — UI polish layer
 * Dark mode toggle (persisted), scroll-reveal animations, animated
 * count-up numbers, and the mobile hamburger menu. Include on every
 * page after theme.css. Safe to include even if a page has none of
 * the optional hooks (data-reveal, data-countup, .hamburger, etc).
 */
(function () {
  document.documentElement.classList.add('js');

  // --- Dark mode ---
  const stored = localStorage.getItem('shield_theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initial = stored || (prefersDark ? 'dark' : 'light');
  if (initial === 'dark') document.documentElement.setAttribute('data-theme', 'dark');

  window.toggleTheme = function () {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('shield_theme', 'light');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('shield_theme', 'dark');
    }
  };

  // --- Mobile menu ---
  window.toggleMobileMenu = function () {
    document.querySelector('.hamburger')?.classList.toggle('open');
    document.querySelector('.mobile-menu')?.classList.toggle('open');
  };

  document.addEventListener('DOMContentLoaded', () => {
    // --- Scroll reveal ---
    const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');
    if (revealEls.length && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
      revealEls.forEach((el) => observer.observe(el));

      // Safety net: never leave content hidden indefinitely.
      setTimeout(() => revealEls.forEach((el) => el.classList.add('in-view')), 5000);
    } else {
      revealEls.forEach((el) => el.classList.add('in-view'));
    }

    // --- Count-up numbers ---
    const countEls = document.querySelectorAll('[data-countup]');
    if (countEls.length && 'IntersectionObserver' in window) {
      const countObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          animateCount(entry.target);
          countObserver.unobserve(entry.target);
        });
      }, { threshold: 0.6 });
      countEls.forEach((el) => countObserver.observe(el));
    } else {
      countEls.forEach(animateCount);
    }

    function animateCount(el) {
      const raw = el.dataset.countup;
      const match = raw.match(/^([^\d]*)([\d,.]+)(.*)$/);
      if (!match) { return; }
      const [, prefix, numStr, suffix] = match;
      const target = parseFloat(numStr.replace(/,/g, ''));
      const decimals = numStr.includes('.') ? numStr.split('.')[1].length : 0;
      const duration = 1400;
      const start = performance.now();

      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = prefix + value.toLocaleString(undefined, {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals,
        }) + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }
  });
})();
