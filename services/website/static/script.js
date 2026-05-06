const sliders = document.querySelectorAll('.slider');

function initSlider(slider) {
  const track = slider.querySelector('.slider-track');
  if (!track) return;

  const slides = Array.from(track.children);
  const prevBtn = slider.querySelector('.prev');
  const nextBtn = slider.querySelector('.next');
  const dotsContainer = slider.querySelector('.slider-dots');
  const autoPlay = slider.dataset.autoplay === 'true';
  const interval = Number(slider.dataset.interval) || 4600;

  if (!slides.length || !prevBtn || !nextBtn || !dotsContainer) return;

  let current = 0;
  let timer = null;
  let touchStartX = null;

  slides.forEach((_, index) => {
    const dot = document.createElement('button');
    dot.type = 'button';
    if (index === 0) dot.classList.add('active');
    dot.addEventListener('click', () => {
      current = index;
      update();
      restartAuto();
    });
    dotsContainer.appendChild(dot);
  });

  function update() {
    track.style.transform = `translate3d(-${current * 100}%, 0, 0)`;

    slides.forEach((slide, index) => {
      slide.classList.toggle('active', index === current);
    });

    dotsContainer.querySelectorAll('button').forEach((dot, index) => {
      dot.classList.toggle('active', index === current);
    });
  }

  function next() {
    current = (current + 1) % slides.length;
    update();
  }

  function prev() {
    current = (current - 1 + slides.length) % slides.length;
    update();
  }

  function restartAuto() {
    if (!autoPlay) return;
    clearInterval(timer);
    timer = setInterval(next, interval);
  }

  nextBtn.addEventListener('click', () => {
    next();
    restartAuto();
  });

  prevBtn.addEventListener('click', () => {
    prev();
    restartAuto();
  });

  slider.addEventListener('mouseenter', () => clearInterval(timer));
  slider.addEventListener('mouseleave', restartAuto);

  slider.addEventListener('touchstart', (event) => {
    touchStartX = event.changedTouches[0].clientX;
  });

  slider.addEventListener('touchend', (event) => {
    if (touchStartX === null) return;
    const touchEndX = event.changedTouches[0].clientX;
    const delta = touchStartX - touchEndX;

    if (Math.abs(delta) > 35) {
      if (delta > 0) {
        next();
      } else {
        prev();
      }
      restartAuto();
    }

    touchStartX = null;
  });

  update();
  restartAuto();
}

sliders.forEach(initSlider);

const parallaxSections = document.querySelectorAll('.parallax-section, .parallax-banner');

function runParallax() {
  const viewportHeight = window.innerHeight;

  parallaxSections.forEach((section) => {
    const rect = section.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > viewportHeight) return;

    const sectionCenter = rect.top + rect.height / 2;
    const viewportCenter = viewportHeight / 2;
    const offset = (sectionCenter - viewportCenter) / viewportHeight;

    section.querySelectorAll('[data-speed]').forEach((layer) => {
      const speed = Number(layer.dataset.speed);
      const y = -offset * speed * 120;
      layer.style.transform = `translate3d(0, ${y}px, 0)`;
    });
  });
}

let ticking = false;

window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      runParallax();
      ticking = false;
    });
    ticking = true;
  }
});

window.addEventListener('resize', () => {
  runParallax();
});
runParallax();

const cursorGlow = document.querySelector('.cursor-glow');

if (window.matchMedia('(pointer:fine)').matches) {
  window.addEventListener('mousemove', (event) => {
    if (cursorGlow) {
      cursorGlow.style.transform = `translate3d(${event.clientX - 120}px, ${event.clientY - 120}px, 0)`;
    }
  });
} else {
  if (cursorGlow) cursorGlow.style.display = 'none';
}

document.querySelectorAll('img[data-fallback]').forEach((img) => {
  img.addEventListener('error', () => {
    const fallback = img.dataset.fallback;
    if (fallback && img.src !== fallback) {
      img.src = fallback;
    }
  });
});

const revealItems = document.querySelectorAll('.reveal-item');

if ('IntersectionObserver' in window && revealItems.length) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  );

  revealItems.forEach((item) => revealObserver.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('revealed'));
}

document.querySelectorAll('[data-tilt]').forEach((card) => {
  card.addEventListener('mousemove', (event) => {
    const rect = card.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const offsetY = event.clientY - rect.top;

    const rotateY = ((offsetX / rect.width) - 0.5) * 12;
    const rotateX = (0.5 - (offsetY / rect.height)) * 10;

    card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(4px)`;
  });

  card.addEventListener('mouseleave', () => {
    card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateZ(0)';
  });
});

document.querySelectorAll('.nav-links a[href="#"], .site-header .btn-outline[href="#"], .brand[href="#"]').forEach((link) => {
  link.addEventListener('click', (event) => event.preventDefault());
});

const tvModuleContainer = document.getElementById('tvModuleContainer');
if (tvModuleContainer) {
  window.setTimeout(() => {
    const hasContent = tvModuleContainer.children.length > 0 || tvModuleContainer.innerHTML.trim().length > 0;
    if (!hasContent) {
      console.warn(
        'Tourvisor модуль не инициализирован. Частые причины: moduleid не активен, модуль не привязан к текущему домену (localhost/file://), либо блокируется расширением.'
      );
    } else {
      console.info('Tourvisor модуль загружен.');
    }
  }, 2500);
}

function stabilizeHashScroll() {
  const hash = window.location.hash;
  if (!hash) return;

  const target = document.querySelector(hash);
  if (!target) return;

  const scrollToTarget = () => {
    target.scrollIntoView({ behavior: 'auto', block: 'start' });
  };

  // First correction after initial layout, second one after async widgets settle.
  window.requestAnimationFrame(scrollToTarget);
  window.setTimeout(scrollToTarget, 900);
  window.setTimeout(scrollToTarget, 2200);
}

window.addEventListener('load', stabilizeHashScroll);

const TOURVISOR_CONFIG = {
  endpoint: '',
  authToken: '',
  source: 'trip-site-form'
};

async function sendLeadToTourvisor(leadPayload) {
  if (!TOURVISOR_CONFIG.endpoint || !TOURVISOR_CONFIG.authToken) {
    console.warn('Tourvisor не настроен: добавьте endpoint и authToken в TOURVISOR_CONFIG');
    return { ok: false, skipped: true };
  }

  const response = await fetch(TOURVISOR_CONFIG.endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOURVISOR_CONFIG.authToken}`
    },
    body: JSON.stringify({
      source: TOURVISOR_CONFIG.source,
      lead: leadPayload
    })
  });

  if (!response.ok) {
    throw new Error(`Tourvisor API error: ${response.status}`);
  }

  return response.json();
}

const tripForm = document.querySelector('.trip-form');

if (tripForm) {
  tripForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(tripForm);
    const payload = {
      name: String(formData.get('name') || '').trim(),
      phone: String(formData.get('phone') || '').trim(),
      email: String(formData.get('email') || '').trim(),
      wishes: String(formData.get('wishes') || '').trim()
    };

    try {
      const response = await fetch('/api/lead', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Lead API error: ${response.status}`);
      }

      try {
        await sendLeadToTourvisor(payload);
      } catch (error) {
        console.error(error);
      }

      tripForm.reset();
      alert('Спасибо! Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время.');
    } catch (error) {
      console.error(error);
      alert('Не удалось отправить заявку. Попробуйте еще раз или свяжитесь с нами по телефону.');
    }
  });
}
