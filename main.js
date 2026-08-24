// ---------- Тема (светлая/тёмная) ----------
const root = document.documentElement;
const toggle = document.getElementById('themeToggle');
const icon = toggle.querySelector('.theme-toggle__icon');

function applyTheme(theme) {
  root.setAttribute('data-theme', theme);
  icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  try { localStorage.setItem('theme', theme); } catch (e) {}
}

const saved = (function () {
  try { return localStorage.getItem('theme'); } catch (e) { return null; }
})();
if (saved) applyTheme(saved);
else applyTheme('light');

toggle.addEventListener('click', () => {
  applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
});

// ---------- Мобильное меню ----------
const burger = document.getElementById('navBurger');
const navLinks = document.getElementById('navLinks');
burger.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach((a) =>
  a.addEventListener('click', () => navLinks.classList.remove('open'))
);

// ---------- Анимация появления ----------
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.section, .hero__inner').forEach((el) => {
  el.classList.add('reveal');
  observer.observe(el);
});

// ---------- Подсветка активного пункта меню ----------
const links = Array.from(document.querySelectorAll('.nav__links a'));
const sections = links
  .map((a) => document.querySelector(a.getAttribute('href')))
  .filter(Boolean);

window.addEventListener('scroll', () => {
  const pos = window.scrollY + 120;
  let current = sections[0];
  for (const sec of sections) {
    if (sec.offsetTop <= pos) current = sec;
  }
  links.forEach((a) => {
    a.style.color = a.getAttribute('href') === '#' + current.id ? 'var(--text)' : '';
  });
}, { passive: true });
