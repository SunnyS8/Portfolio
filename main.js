// Лёгкая анимация появления секций при скролле
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

// Подсветка активного пункта меню
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
