// Обработка мобильного меню
document.addEventListener('DOMContentLoaded', function() {
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const mobileMenuClose = document.getElementById('mobile-menu-close');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileNavLinks = document.querySelectorAll('.mobile-nav .nav-link');
  
  // Открыть меню
  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', function() {
      mobileMenu.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }
  
  // Закрыть меню
  if (mobileMenuClose) {
    mobileMenuClose.addEventListener('click', function() {
      mobileMenu.classList.remove('active');
      document.body.style.overflow = '';
    });
  }
  
  // Закрыть меню при клике на ссылку
  mobileNavLinks.forEach(link => {
    link.addEventListener('click', function() {
      mobileMenu.classList.remove('active');
      document.body.style.overflow = '';
    });
  });
  
  // Обработка активных ссылок в меню
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');
  
  function highlightNavLink() {
    const scrollPosition = window.scrollY + 100;
    
    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      const sectionId = section.getAttribute('id');
      
      if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + sectionId) {
            link.classList.add('active');
          }
        });
      }
    });
  }
  
  window.addEventListener('scroll', highlightNavLink);
  highlightNavLink();
  
  // Галерея и модальное окно
  const galleryItems = document.querySelectorAll('.gallery-item');
  const modal = document.getElementById('gallery-modal');
  const modalClose = document.querySelector('.modal-close');
  const imageContainer = document.querySelector('.image-container');
  const modalTitle = document.querySelector('.modal-title');
  
  galleryItems.forEach(item => {
    item.addEventListener('click', function() {
      const type = this.getAttribute('data-type');
      const src = this.getAttribute('data-src');
      const title = this.querySelector('.gallery-caption h3').textContent;
      
      // Очистить контейнер
      imageContainer.innerHTML = '';
      
      if (type === 'image') {
        const img = document.createElement('img');
        img.src = src;
        img.alt = title;
        imageContainer.appendChild(img);
      } else if (type === 'video') {
        const video = document.createElement('video');
        video.src = src;
        video.controls = true;
        video.autoplay = true;
        imageContainer.appendChild(video);
      }
      
      modalTitle.textContent = title;
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  });
  
  if (modalClose) {
    modalClose.addEventListener('click', function() {
      modal.classList.remove('active');
      document.body.style.overflow = '';
      
      // Остановить видео если оно воспроизводится
      const video = imageContainer.querySelector('video');
      if (video) {
        video.pause();
      }
    });
  }
  
  // Закрыть модальное окно при клике вне его содержимого
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
      
      // Остановить видео если оно воспроизводится
      const video = imageContainer.querySelector('video');
      if (video) {
        video.pause();
      }
    }
  });
});

// Плавная прокрутка для якорных ссылок
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    
    const targetId = this.getAttribute('href');
    const targetElement = document.querySelector(targetId);
    
    if (targetElement) {
      window.scrollTo({
        top: targetElement.offsetTop - 80,
        behavior: 'smooth'
      });
    }
  });
});