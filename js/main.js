/* ============================================================
    [Master Scripts]

    Theme Name:     BizVision     
    Theme URL:      http://
    Description:    BizVision -  Finance & Business Consulting HTML Template 
    Version:        1.0.0

============================================================== */ 

'use strict';
(function ($) {
  // Gsap Plugin Register
  gsap.registerPlugin(ScrollTrigger);

  /* ========================================
     Navbar sticky Js
   ======================================== */
  if ($('.navbar').length) {
    gsap.to(".navbar", {
      scrollTrigger: {
        trigger: ".navbar",
        start: "top+=2 top",
        endTrigger: "body",
        end: "bottom 0",
        pin: true,
        pinSpacing: false,
        toggleClass: { targets: ".navbar", className: "sticky" }, 
      },
    });
  }

  /* ========================================
     Navbar Links Active  Js
   ======================================== */
  if ($('.navbar-nav').length) {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, .dropdown-menu .dropdown-item');
    const removeActiveClass = () => {
      navLinks.forEach((link) => link.classList.remove('active'));
    };
    const setActiveLink = () => {
      const currentPath = window.location.pathname;
      removeActiveClass();

      navLinks.forEach((link) => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath.endsWith(linkPath)) {
          link.classList.add('active');

          const parentDropdown = link.closest('.dropdown-menu')?.previousElementSibling;
          if (parentDropdown) {
            parentDropdown.classList.add('active');
          }
        }
      });
    };
    setActiveLink();
  }

  /* ========================================
   banner slider Js
  ======================================== */
  const bannerSliderSwiper = new Swiper('.banner-slider', {
    slidesPerView: 1,
    loop: true,
    pagination: false,
    effect: "fade",
    autoplay: {
      delay: 5000,
      disableOnInteraction: false,
    },
    autoplay: false,
    on: {
      init: animateActiveSlide,
      slideChangeTransitionStart: animateActiveSlide,
    },
  });

  function animateActiveSlide() {
    const activeSlide = document.querySelector('.swiper-slide-active');
    if (!activeSlide) return;

    const elements = {
      title: activeSlide.querySelector('h1'),
      subTitle: activeSlide.querySelector('.banner-sub-title'),
      btnGroup: activeSlide.querySelector('.button-group'),
      borderShape: activeSlide.querySelector('.border-shape'),
      img: activeSlide.querySelector('.banner-image img'),
      char_come: activeSlide.querySelector('h1'),
    };

    gsap.killTweensOf(Object.values(elements));

    const animations = [
      {
        element: elements.subTitle,
        from: { opacity: 0, x: -50 },
        to: { opacity: 1, x: 0, duration: 1, ease: "power3.out", delay: 0.4 },
      },
      {
        element: elements.btnGroup,
        from: { opacity: 0, scale: 0.8 },
        to: { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.6 },
      },
      {
        element: elements.borderShape,
        from: { scale: 0.3, opacity: 0 },
        to: { scale: 1, opacity: 1, duration: 1, ease: "power3.out", delay: 0.7 },
      },
      {
        element: elements.img,
        from: { opacity: 0, x: 50 },
        to: { opacity: 1, x: 0, duration: 1, ease: "power3.out", delay: 0.2 },
      },
    ];

    animations.forEach(({ element, from, to }) => {
      if (element) gsap.fromTo(element, from, to);
    });

    if (elements.char_come) {
      const splitChar = new SplitText(elements.char_come, { type: "chars, words" });
      const staggerDuration = window.innerWidth < 768 ? 0.05 : 0.03;

      gsap.timeline({
        scrollTrigger: {
          trigger: elements.char_come,
          start: "top 90%",
          end: "bottom 60%",
          scrub: false,
          toggleActions: "play none none none",
        },
      }).from(splitChar.chars, {
        duration: 0.8,
        x: 70,
        autoAlpha: 0,
        stagger: staggerDuration,
      });
    }
  }

  /* ========================================
    service slider Js
  ======================================== */
  const servicesOneSwiper = new Swiper(".services-one-slid", {
    slidesPerView: 3,
    spaceBetween: 10,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  /* ========================================
    case slider Js
  ======================================== */
  const caseOneSwiper = new Swiper(".case-studies", {
    slidesPerView: 3,
    spaceBetween: 24,
    pagination: {
      el: ".swiper-pagination",
      dynamicBullets: true,
    },
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  /* ========================================
    team slider Js
  ======================================== */
  const teamOneSwiper = new Swiper(".team-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    pagination: {
      el: ".swiper-number",
      type: "fraction",
    },
    navigation: {
      nextEl: ".slid-btn-next",
      prevEl: ".slid-btn-prev",
    },
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  const teamThreeSwiper = new Swiper(".team-three-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 3,
      },
      1200: {
        slidesPerView: 4,
      }
    },
  });

  const teamFourSwiper = new Swiper(".team-four-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  /* ========================================
    blog slider Js
  ======================================== */
  const blogOneSwiper = new Swiper(".blog-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  /* ========================================
    blog slider Js
  ======================================== */
  const blogTwoSwiper = new Swiper(".blogs-two-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 3,
      }
    },
  });

  /* ========================================
    feedback slider Js
  ======================================== */
  const feedbackOneSwiper = new Swiper('.feedback-slide', {
    slidesPerView: 1,
    loop: true,
    pagination: false,
    spaceBetween: 24,
    pagination: {
      el: ".swiper-pagination",
      dynamicBullets: true,
    },
    breakpoints: {
      '1200': {
        slidesPerView: 2,
      },
      '991': {
        slidesPerView: 2,
      },
      '0': {
        slidesPerView: 1,
      }
    },

  });

  /* ========================================
    feedback two slider Js
  ======================================== */
  const feedbackTwoSwiper = new Swiper('.feedback-two-slide', {
    slidesPerView: 1,
    loop: true,
    spaceBetween: 24,
    speed: 700,
    pagination: {
      el: ".swiper-number",
      type: "fraction",
    },
    navigation: {
      nextEl: ".slid-btn-next",
      prevEl: ".slid-btn-prev",
    },
    autoplay: {
      delay: 5000,
      disableOnInteraction: false,
    },
    breakpoints: {
      1200: {
        slidesPerView: 2,
      },
      0: {
        slidesPerView: 1,
      },
    },
  });

  /* ========================================
    Brand slider Js
  ======================================== */
  const brandSwiper = new Swiper('.brand-active-slid', {
    loop: true,
    slidesPerView: 'auto',
    centeredSlides: true,
    allowTouchMove: false,
    spaceBetween: 30,
    speed: 4000,
    autoplay: {
      delay: 0,
      disableOnInteraction: false,
    },
  });

  /* ========================================
    team two slider Js
  ======================================== */
  const teamTwoSwiper = new Swiper(".team-two-slide", {
    slidesPerView: 3,
    spaceBetween: 24,
    breakpoints: {
      0: {
        slidesPerView: 1,
      },
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 3,
      },
      1200: {
        slidesPerView: 4,
      }
    },
  });


  /* ========================================
    Cursor Design Js
  ======================================== */
  if (document.querySelector('.cursor, .cursor-trail')) {
    const cursor = document.querySelector('.cursor');
    const cursorTrail = document.querySelector('.cursor-trail');
    const interactiveElements = document.querySelectorAll('a, button, .cursor-slider');

    // Cursor movement
    document.addEventListener('mousemove', (event) => {
      gsap.to(cursor, { x: event.clientX, y: event.clientY, duration: 0.1 });
      gsap.to(cursorTrail, { x: event.clientX, y: event.clientY, duration: 0.3, ease: 'power2.out' });
    });

    // Interactive elements hover effects
    interactiveElements.forEach((el) => {
      el.addEventListener('mouseenter', () => {
        gsap.to(cursor, { scale: 1.05 });
        gsap.to(cursorTrail, { scale: 1.7, backgroundColor: 'rgba(255, 255, 255, 0.0)' });
      });

      el.addEventListener('mouseleave', () => {
        gsap.to(cursor, { scale: 1 });
        gsap.to(cursorTrail, { scale: 1, backgroundColor: 'rgba(255, 255, 255, 0.308)' });
      });
    });
  }

  /* ========================================
    cursor Js
  ======================================== */
  if (document.querySelector('.cursor-slider')) {
    const cursorSlider = document.querySelector('.cursor-slider');
    const body = document.body;
    const toggleClass = 'show-custom-cursor';
    const mediaQuery = window.matchMedia('(hover: hover)');

    document.addEventListener('pointermove', (e) => {
      const isHoverEnabled = mediaQuery.matches;
      const isInsideCarousel = e.target.closest('.carousel-wrapper');

      if (isHoverEnabled && isInsideCarousel) {
        body.classList.add(toggleClass);
        cursorSlider.style.setProperty('--cursor-x', `${e.clientX}px`);
        cursorSlider.style.setProperty('--cursor-y', `${e.clientY}px`);
      } else {
        body.classList.remove(toggleClass);
      }
    });
  }

  /* ========================================
    Title animation Js
  ======================================== */
  if ($(".title-animation").length) {
    const char_come = gsap.utils.toArray(".title-animation");
    char_come.forEach((char_come) => {
      const split_char = new SplitText(char_come, {
        type: "chars, words",
        lineThreshold: 0.5,
      });
      const staggerDuration = window.innerWidth < 768 ? 0.05 : 0.03;
      const tl2 = gsap.timeline({
        scrollTrigger: {
          trigger: char_come,
          start: "top 90%",
          end: "bottom 60%",
          scrub: false,
          markers: false,
          toggleActions: "play none none none",
        },
      });
      tl2.from(split_char.chars, {
        duration: 0.8,
        x: 70,
        autoAlpha: 0,
        stagger: staggerDuration,
      });
    });
  }

  /* ========================================
    Sub title animation Js
  ======================================== */
  if ($(".sub-animation").length) {
    const animateTextFromBottom = gsap.utils.toArray(".sub-animation");
    animateTextFromBottom.forEach((item) => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: item,
          start: "top 90%",
          end: "bottom 60%",
          toggleActions: "play none none none",
        },
      });
      const splitText = new SplitText(item, { type: "chars, words, lines" });
      splitText.split({ type: "words" });
      tl.from(splitText.words, {
        duration: 1,
        y: 50,
        autoAlpha: 0,
        stagger: 0.05,
        onComplete: () => {
          splitText.revert();
        },
      });
    });
  }

  /* ========================================
    3d animation Js
  ======================================== */
  if ($(".animate-3d").length) {
    const animateLine3d = gsap.utils.toArray(".animate-3d");
    animateLine3d.forEach((item) => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: item,
          start: "top 90%",
          end: "bottom 60%",
          toggleActions: "play none none none",
        },
      });
      const animateLine3dSplitted = new SplitText(item, { type: "chars, words, lines" });
      gsap.set(item, { perspective: 400 });
      animateLine3dSplitted.split({ type: "lines" });
      tl.from(animateLine3dSplitted.lines, {
        duration: 1,
        delay: 0.3,
        opacity: 0,
        rotationX: -80,
        force3D: true,
        transformOrigin: "top center -50",
        stagger: 0.1,
        onComplete: () => {
          animateLine3dSplitted.revert();
        },
      });
    });
  }

  /* ========================================
    Button and text animation Js
  ======================================== */
  if ($(".btn-text-animate").length) {
    const animateTextFromBottom = gsap.utils.toArray(".btn-text-animate");
    animateTextFromBottom.forEach((item) => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: item,
          start: "top 90%",
          end: "bottom 60%",
          toggleActions: "play none none none",
        },
      });
      const animateTextFromBottomSplitted = new SplitText(item, { type: "chars, words, lines" });
      animateTextFromBottomSplitted.split({ type: "words" });
      tl.from(animateTextFromBottomSplitted.words, {
        duration: 1,
        y: 50,
        autoAlpha: 0,
        stagger: 0.05,
        onComplete: () => {
          animateTextFromBottomSplitted.revert();
        },
      });
    });
  }

  /* ========================================
    Generalized Fade-In animation Js
  ======================================== */
  function fadeIn(targets, properties = {}, options = {}) {
    const elements = gsap.utils.toArray(targets);
    if (elements.length === 0) return;
    gsap.from(elements, {
      opacity: properties.opacity ?? 0,
      y: properties.y ?? 0,
      x: properties.x ?? 0,
      duration: properties.duration ?? 1,
      delay: properties.delay ?? 0,
      stagger: options.stagger ?? 0.15,
      ease: options.ease ?? "power2.out",
      scrollTrigger: {
        trigger: elements,
        start: options.start || "top 90%",
        end: options.end || "bottom 60%",
        toggleActions: options.toggleActions || "play none none none",
      },
    });
  }
  function fadeInElements() {
    fadeIn(".animate-fadeInBottom", { y: 50 }, { stagger: 0.1 });
    fadeIn(".fadeIn_50", { y: 50 });
    fadeIn(".fadeIn_promo", { y: 80 });
    fadeIn(".fadeDown_testimonial", { y: 80 });
    fadeIn(".fadeIn_every", { y: 100 }, { stagger: 0.25 });
    fadeIn(".fadeIn_pricing", { y: 100 }, { stagger: 0.25 });
    fadeIn(".team-section__item", { y: 100 }, { stagger: 0.25 });
    fadeIn(".testimonial-slide__item", { y: 90 }, { stagger: 0.15 });

    fadeIn(".fadeDown_50", { x: -50 });
    fadeIn(".fadeDown_80", { x: -80 });
    fadeIn(".fadeDown_100", { x: -100 });
    fadeIn(".fadeIn_cases", { x: -100 });
    fadeIn(".fadeIn_faq", { x: -100 });
    fadeIn(".fadeIn_faq2", { x: 100 });
    fadeIn(".fadeIn_content", { x: -100 });

    fadeIn(".input-box", { duration: 2, delay: 0.25 }, { stagger: 0.25 });
    fadeIn(".fadeIn_1", { duration: 2, delay: 0.25 }, { stagger: 0.25 });
    fadeIn(".fadeIn_human", { duration: 2, delay: 0.25 }, { stagger: 0.25 });
    fadeIn(".blog-section__item", { duration: 1.8, delay: 0.20 }, { stagger: 0.25 });
  }
  fadeInElements();


  if ($(".reveal-img").length > 0) {
    gsap.utils.toArray(".reveal-img").forEach((el) => {
      gsap.to(el, {
        scrollTrigger: {
          trigger: el,
          start: "top 80%",
          markers: false,
          onEnter: () => {
            el.classList.add("reveal-img-active");
          },
        },
      });
    });
  }

  const imageParallax = document.querySelectorAll(".parallax-image");

  if (imageParallax.length > 0) {
    imageParallax.forEach(function (element) {
      const wrapper = document.createElement("div");
      wrapper.className = "parallax-image-wrap";

      const innerWrapper = document.createElement("div");
      innerWrapper.className = "parallax-image-inner";

      element.parentNode.insertBefore(wrapper, element);
      wrapper.appendChild(innerWrapper);
      innerWrapper.appendChild(element);

      wrapper.style.overflow = "hidden";

      const animImageParallax = element;
      const imgParallaxWrapper = wrapper;
      const innerWrap = innerWrapper;

      const tlImageParallax = gsap.timeline({
        scrollTrigger: {
          trigger: imgParallaxWrapper,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
          onEnter: animImgParallaxRefresh,
        },
      });

      tlImageParallax.to(animImageParallax, {
        yPercent: 35,
        ease: "none",
      });

      function animImgParallaxRefresh() {
        tlImageParallax.scrollTrigger.refresh();
      }

      const tlZoomIn = gsap.timeline({
        scrollTrigger: {
          trigger: imgParallaxWrapper,
          start: "top 99%",
        },
      });

      tlZoomIn.from(innerWrap, {
        duration: 1.5,
        opacity: 0,
        scale: 1.2,
        ease: "power2.out",
        clearProps: "all",
      });
    });
  }

  /* ========================================
    Odometer Counter Up Js
   ======================================== */
  // data-odometer-final
  if ($('.odometer').length) {
    $(window).on('scroll', function () {
      $('.odometer').each(function () {
        if ($(this).isInViewport()) {
          if (!$(this).data('odometer-started')) {
            $(this).data('odometer-started', true);
            this.innerHTML = $(this).data('odometer-final');
          }
        }
      });
    });
  }
  // isInViewport helper function
  $.fn.isInViewport = function () {
    let elementTop = $(this).offset().top;
    let elementBottom = elementTop + $(this).outerHeight();
    let viewportTop = $(window).scrollTop();
    let viewportBottom = viewportTop + $(window).height();
    return elementBottom > viewportTop && elementTop < viewportBottom;
  };


  /* ========================================
     Scroll back to top  Js
   ======================================== */
  if ($('.progress-wrap').length) {
    const progressPath = document.querySelector('.progress-wrap path');
    const pathLength = progressPath.getTotalLength();

    // Set up the initial stroke styles
    progressPath.style.transition = 'none';
    progressPath.style.strokeDasharray = `${pathLength} ${pathLength}`;
    progressPath.style.strokeDashoffset = pathLength;
    progressPath.getBoundingClientRect();

    // Set transition for stroke-dashoffset
    progressPath.style.transition = 'stroke-dashoffset 10ms linear';

    const updateProgress = () => {
      const scroll = $(window).scrollTop();
      const height = $(document).height() - $(window).height();
      const progress = pathLength - (scroll * pathLength / height);
      progressPath.style.strokeDashoffset = progress;
    };

    updateProgress();
    $(window).on('scroll', updateProgress);

    const offset = 50;
    const duration = 550;

    $(window).on('scroll', () => {
      $('.progress-wrap').toggleClass('active-progress', $(window).scrollTop() > offset);
    });

    $('.progress-wrap').on('click', (event) => {
      event.preventDefault();
      $('html, body').animate({ scrollTop: 0 }, duration);
    });
  }
  // progress bar animate numbers
  if ($('.skill-container__item').length) {
    function animateNumbers(element) {
      const target = +element.getAttribute('data-target');
      const duration = 1500; // 1.5 second
      const step = target / (duration / 20);

      let current = 0;
      const interval = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(interval);
        }
        element.textContent = Math.round(current) + "%";
      }, 20);
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const progressBar = entry.target.querySelector('.progress-bar');
            const percentageText = entry.target.querySelector('.percentage');

            const targetWidth = percentageText.getAttribute('data-target') + '%';
            progressBar.style.width = targetWidth;
            progressBar.setAttribute('aria-valuenow', targetWidth);

            animateNumbers(percentageText);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    document.querySelectorAll('.skill-container__item').forEach((item) => observer.observe(item));
  }

  document.addEventListener('DOMContentLoaded', () => {
    const navPills = document.querySelector('.nav-pills');
    if (navPills) {
      const links = navPills.querySelectorAll('.nav-link');
      const indicator = navPills.querySelector('.nav-indicator');

      function updateIndicator(el) {
        if (el) {
          indicator.style.width = `${el.offsetWidth}px`;
          indicator.style.left = `${el.offsetLeft}px`;
        }
      }

      const activeLink = navPills.querySelector('.nav-link.active');
      if (activeLink) updateIndicator(activeLink);

      links.forEach(link => {
        link.addEventListener('click', () => {
          navPills.querySelector('.nav-link.active')?.classList.remove('active');
          link.classList.add('active');
          updateIndicator(link);
        });
      });
    }
  });

  $('.bg-img').css('background-image', function () {
    var bg = 'url(' + $(this).data('background-image') + ')';
    return bg;
  });

  $('.video-play-btn').magnificPopup({
    disableOn: 700,
    type: 'iframe',
    mainClass: 'mfp-fade',
    removalDelay: 160,
    preloader: false,
    fixedContentPos: false
  });

  $('.services-one-box').hover(function () {
    $('.services-one-box').removeClass('active');
    $(this).addClass('active');
  });

  const scrollReveal = ScrollReveal({
    origin: 'top', distance: '60px', duration: 1300, delay: 100, mobile: false,
  })
  scrollReveal.reveal('.top-reveal', {
    delay: 60, distance: '60px', origin: 'top', interval: 100, mobile: false,
  })
  scrollReveal.reveal('.left-reveal', {
    delay: 60, origin: 'left', interval: 100, mobile: false,
  })
  scrollReveal.reveal('.right-reveal', {
    delay: 60, origin: 'right', interval: 100, mobile: false,
  })
  scrollReveal.reveal('.bottom-reveal', {
    delay: 60, origin: 'bottom', interval: 100, mobile: false,
  })
  scrollReveal.reveal('.scaleUp', {
    scale: 0.85, mobile: false,
  })

  /* ========================================
      Preloader Js
  ======================================== */
  window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    preloader.style.transition = 'height 0.5s, opacity 1s';
    preloader.style.opacity = '0';
    preloader.style.height = '0';
    preloader.style.borderBottomLeftRadius = '100%';
    preloader.style.borderBottomRightRadius = '100%';
    setTimeout(() => {
      preloader.style.display = 'none';
    }, 500);
  });

})(jQuery);

/* ========================================
    LGPD Cookie Consent Banner
    Elegant, minimal, LGPD-compliant
======================================== */
(function(){
  var STORAGE_KEY = 'audiper_cookie_consent';
  var STORAGE_PREFS = 'audiper_cookie_prefs';
  var CONSENT_DAYS = 180;

  // Don't show if already consented
  var stored = localStorage.getItem(STORAGE_KEY);
  if(stored){
    try{
      var data = JSON.parse(stored);
      if(data.timestamp && (Date.now() - data.timestamp) < CONSENT_DAYS * 86400000) return;
    }catch(e){}
  }

  // Inject CSS
  var style = document.createElement('style');
  style.textContent = [
    '#audiper-cookie-banner{position:fixed;bottom:0;left:0;right:0;z-index:9996;transform:translateY(100%);opacity:0;transition:transform .5s cubic-bezier(.22,1,.36,1),opacity .4s ease;font-family:"Inter",sans-serif}',
    '#audiper-cookie-banner.visible{transform:translateY(0);opacity:1}',
    '#audiper-cookie-banner.hiding{transform:translateY(100%);opacity:0}',
    '.acb-wrap{background:#fff;border-top:1px solid #e5e7eb;box-shadow:0 -4px 32px rgba(0,0,0,.08)}',
    '.acb-main{max-width:1200px;margin:0 auto;padding:20px 24px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}',
    '.acb-icon{flex-shrink:0;width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#c41a1a10,#c41a1a20);display:flex;align-items:center;justify-content:center;font-size:20px}',
    '.acb-text{flex:1;min-width:280px}',
    '.acb-text p{font-size:.9rem;color:#444;line-height:1.6;margin:0}',
    '.acb-text a{color:#c41a1a;text-decoration:underline;text-underline-offset:2px;font-weight:500}',
    '.acb-text a:hover{opacity:.8}',
    '.acb-btns{display:flex;gap:8px;flex-shrink:0;flex-wrap:wrap}',
    '.acb-btn{font-family:"Figtree",sans-serif;font-weight:600;font-size:.85rem;padding:10px 20px;border-radius:8px;border:none;cursor:pointer;transition:all .2s;white-space:nowrap}',
    '.acb-btn-accept{background:#c41a1a;color:#fff}',
    '.acb-btn-accept:hover{background:#a51515;transform:translateY(-1px);box-shadow:0 4px 12px rgba(196,26,26,.3)}',
    '.acb-btn-reject{background:#f3f4f6;color:#333}',
    '.acb-btn-reject:hover{background:#e5e7eb}',
    '.acb-btn-prefs{background:transparent;color:#666;border:1px solid #ddd;padding:10px 16px}',
    '.acb-btn-prefs:hover{border-color:#c41a1a;color:#c41a1a}',
    '.acb-promo{border-top:1px solid #f0f0f0;background:#fafafa}',
    '.acb-promo-inner{max-width:1200px;margin:0 auto;padding:10px 24px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}',
    '.acb-promo-badge{font-family:"JetBrains Mono",monospace;font-size:.65rem;font-weight:600;padding:3px 10px;border-radius:12px;background:#c41a1a10;color:#c41a1a;text-transform:uppercase;letter-spacing:1px;white-space:nowrap}',
    '.acb-promo p{font-size:.82rem;color:#666;margin:0;flex:1}',
    '.acb-promo p strong{color:#333;font-weight:600}',
    '.acb-promo a{font-family:"Figtree",sans-serif;font-weight:600;font-size:.8rem;color:#c41a1a;text-decoration:none;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}',
    '.acb-promo a:hover{text-decoration:underline}',
    /* Preferences panel */
    '#acb-prefs-panel{display:none;max-width:1200px;margin:0 auto;padding:0 24px 20px}',
    '#acb-prefs-panel.open{display:block}',
    '.acb-prefs-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}',
    '.acb-pref-item{background:#f8f8f8;border-radius:10px;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}',
    '.acb-pref-info h5{font-family:"Figtree",sans-serif;font-size:.85rem;font-weight:700;color:#111;margin:0 0 2px}',
    '.acb-pref-info span{font-size:.75rem;color:#888}',
    '.acb-toggle{position:relative;width:44px;height:24px;flex-shrink:0}',
    '.acb-toggle input{opacity:0;width:0;height:0}',
    '.acb-toggle-slider{position:absolute;inset:0;background:#ddd;border-radius:24px;cursor:pointer;transition:background .2s}',
    '.acb-toggle-slider::before{content:"";position:absolute;width:18px;height:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:transform .2s;box-shadow:0 1px 3px rgba(0,0,0,.15)}',
    '.acb-toggle input:checked+.acb-toggle-slider{background:#c41a1a}',
    '.acb-toggle input:checked+.acb-toggle-slider::before{transform:translateX(20px)}',
    '.acb-toggle input:disabled+.acb-toggle-slider{background:#c41a1a;opacity:.6;cursor:not-allowed}',
    '.acb-toggle input:disabled+.acb-toggle-slider::before{transform:translateX(20px)}',
    /* Mobile */
    '@media(max-width:768px){.acb-main{padding:16px;gap:16px;flex-direction:column;align-items:stretch}.acb-icon{display:none}.acb-btns{justify-content:stretch}.acb-btn{flex:1;text-align:center;padding:12px 12px}.acb-promo-inner{flex-direction:column;align-items:flex-start;gap:8px;padding:12px 16px}}'
  ].join('\n');
  document.head.appendChild(style);

  // Build banner HTML
  var banner = document.createElement('div');
  banner.id = 'audiper-cookie-banner';
  banner.setAttribute('role','dialog');
  banner.setAttribute('aria-label','Aviso de Cookies');

  // Determine if we're in a subdirectory (blog/)
  var isSubdir = window.location.pathname.indexOf('/blog/') !== -1;
  var privLink = isSubdir ? '../privacidade.html' : 'privacidade.html';
  var contatoLink = isSubdir ? '../contato.html' : 'contato.html';
  var iaLink = isSubdir ? '../ia-negocios.html' : 'ia-negocios.html';

  banner.innerHTML = [
    '<div class="acb-wrap">',
    '  <div class="acb-main">',
    '    <div class="acb-icon">\uD83D\uDD12</div>',
    '    <div class="acb-text">',
    '      <p>Utilizamos cookies para melhorar sua experi\u00EAncia, personalizar conte\u00FAdo e analisar nosso tr\u00E1fego. Voc\u00EA pode gerenciar suas prefer\u00EAncias a qualquer momento. <a href="'+privLink+'">Pol\u00EDtica de Privacidade</a></p>',
    '    </div>',
    '    <div class="acb-btns">',
    '      <button class="acb-btn acb-btn-accept" id="acb-accept">Aceitar</button>',
    '      <button class="acb-btn acb-btn-reject" id="acb-reject">Rejeitar</button>',
    '      <button class="acb-btn acb-btn-prefs" id="acb-toggle-prefs">Personalizar</button>',
    '    </div>',
    '  </div>',
    '  <div id="acb-prefs-panel">',
    '    <div class="acb-prefs-grid">',
    '      <div class="acb-pref-item">',
    '        <div class="acb-pref-info"><h5>Essenciais</h5><span>Sempre ativos</span></div>',
    '        <label class="acb-toggle"><input type="checkbox" checked disabled/><span class="acb-toggle-slider"></span></label>',
    '      </div>',
    '      <div class="acb-pref-item">',
    '        <div class="acb-pref-info"><h5>Desempenho</h5><span>An\u00E1lise an\u00F4nima</span></div>',
    '        <label class="acb-toggle"><input type="checkbox" data-cookie="performance"/><span class="acb-toggle-slider"></span></label>',
    '      </div>',
    '      <div class="acb-pref-item">',
    '        <div class="acb-pref-info"><h5>Funcionalidade</h5><span>Prefer\u00EAncias salvas</span></div>',
    '        <label class="acb-toggle"><input type="checkbox" data-cookie="functionality"/><span class="acb-toggle-slider"></span></label>',
    '      </div>',
    '      <div class="acb-pref-item">',
    '        <div class="acb-pref-info"><h5>Marketing</h5><span>Conte\u00FAdo relevante</span></div>',
    '        <label class="acb-toggle"><input type="checkbox" data-cookie="marketing"/><span class="acb-toggle-slider"></span></label>',
    '      </div>',
    '    </div>',
    '    <div style="text-align:right;margin-top:12px">',
    '      <button class="acb-btn acb-btn-accept" id="acb-save-prefs">Salvar prefer\u00EAncias</button>',
    '    </div>',
    '  </div>',
    '</div>',
    '<div class="acb-promo">',
    '  <div class="acb-promo-inner">',
    '    <span class="acb-promo-badge">LGPD</span>',
    '    <p><strong>Sua empresa est\u00E1 adequada \u00E0 LGPD?</strong> A AUD\u00CDPER implementa programas de conformidade digital e audita a prote\u00E7\u00E3o de dados do seu neg\u00F3cio.</p>',
    '    <a href="'+contatoLink+'">Saiba mais <i class="fa-solid fa-arrow-right" style="font-size:11px"></i></a>',
    '  </div>',
    '</div>'
  ].join('\n');

  document.body.appendChild(banner);

  // Show with delay
  setTimeout(function(){
    banner.classList.add('visible');
  }, 1500);

  // Functions
  function saveConsent(type, prefs){
    localStorage.setItem(STORAGE_KEY, JSON.stringify({type:type,timestamp:Date.now()}));
    if(prefs) localStorage.setItem(STORAGE_PREFS, JSON.stringify(prefs));
    banner.classList.add('hiding');
    banner.classList.remove('visible');
    setTimeout(function(){ banner.remove(); }, 600);
  }

  function getPrefs(){
    var prefs = {essential:true, performance:false, functionality:false, marketing:false};
    var checkboxes = banner.querySelectorAll('[data-cookie]');
    checkboxes.forEach(function(cb){
      prefs[cb.getAttribute('data-cookie')] = cb.checked;
    });
    return prefs;
  }

  // Event Listeners
  document.getElementById('acb-accept').addEventListener('click', function(){
    saveConsent('all', {essential:true,performance:true,functionality:true,marketing:true});
  });

  document.getElementById('acb-reject').addEventListener('click', function(){
    saveConsent('essential', {essential:true,performance:false,functionality:false,marketing:false});
  });

  document.getElementById('acb-toggle-prefs').addEventListener('click', function(){
    var panel = document.getElementById('acb-prefs-panel');
    panel.classList.toggle('open');
    this.textContent = panel.classList.contains('open') ? 'Fechar' : 'Personalizar';
  });

  document.getElementById('acb-save-prefs').addEventListener('click', function(){
    saveConsent('custom', getPrefs());
  });
})();
