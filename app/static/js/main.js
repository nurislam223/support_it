// main.js
document.addEventListener('DOMContentLoaded', function () {
  // Мобильное меню
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  const mainContent = document.getElementById('mainContent');
  const menuIcon = document.querySelector('.menu-icon');
  const closeIcon = document.querySelector('.close-icon');

  function toggleMenu() {
    const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
    mobileMenuBtn.setAttribute('aria-expanded', !isExpanded);
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');

    if (!isExpanded) {
      menuIcon.style.display = 'none';
      closeIcon.style.display = 'block';
    } else {
      menuIcon.style.display = 'block';
      closeIcon.style.display = 'none';
    }

    if (window.innerWidth >= 769) {
      if (!isExpanded) {
        mainContent.classList.add('with-sidebar');
      } else {
        mainContent.classList.remove('with-sidebar');
      }
    }

    if (window.innerWidth < 769) {
      document.body.style.overflow = isExpanded ? 'auto' : 'hidden';
    }
  }

  function closeMenu() {
    mobileMenuBtn.setAttribute('aria-expanded', 'false');
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    mainContent.classList.remove('with-sidebar');
    menuIcon.style.display = 'block';
    closeIcon.style.display = 'none';
    document.body.style.overflow = 'auto';
  }

  mobileMenuBtn.addEventListener('click', toggleMenu);
  overlay.addEventListener('click', closeMenu);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('active')) {
      closeMenu();
    }
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 769 && sidebar.classList.contains('active')) {
      mainContent.classList.add('with-sidebar');
    } else {
      mainContent.classList.remove('with-sidebar');
      document.body.style.overflow = 'auto';
    }

    if (window.innerWidth >= 769) {
      menuIcon.style.display = 'block';
      closeIcon.style.display = 'none';
    }
  });

  if ('ontouchstart' in window) {
    document.documentElement.classList.add('touch-device');
  }

  // Ленивая загрузка изображений с fallback
  const images = document.querySelectorAll('.card-image');
  const wrappers = document.querySelectorAll('.card-image-wrapper');

  wrappers.forEach(wrapper => {
    wrapper.classList.add('loading');
  });

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        const wrapper = img.closest('.card-image-wrapper');
        wrapper.classList.remove('loading');

        img.addEventListener('load', () => {
          img.classList.add('loaded');
          imageObserver.unobserve(img);
        });

        img.addEventListener('error', () => {
          img.style.display = 'none';
          imageObserver.unobserve(img);
        });
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));

  // Доступность навигации
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        item.click();
      }
    });

    item.addEventListener('click', () => {
      if (window.innerWidth < 769) {
        closeMenu();
      }
    });
  });
});