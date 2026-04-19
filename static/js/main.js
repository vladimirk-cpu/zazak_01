(function () {
  function initPhoneMasks() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    if (typeof Inputmask === 'undefined') return;

    // Определяем правило: первая цифра кода (после +7) должна быть только 9
    Inputmask.extendDefinitions({
      'f': {
        validator: "[9]",
        cardinality: 1
      }
    });

    phoneInputs.forEach(input => {
      Inputmask({
        mask: '+7 (f99) 999-99-99',
        clearMaskOnLostFocus: true,
        clearIncomplete: true,
        showMaskOnHover: false,
        showMaskOnFocus: true,
        onBeforeMask: function (value, opts) {
          // Если вставляется номер, начинающийся с +7 или 8, обрезаем префикс
          return value.replace(/^(\+7|8)/, '');
        },
        onKeyDown: function (e, buffer, opts) {
          const input = e.target;
          // Если курсор в начале кода (позиция 4 после "+7 (") и нажата 8 или 7 — игнорируем
          if (input.selectionStart === 4 && (e.key === '8' || e.key === '7')) {
            e.preventDefault();
          }
        },
        oncomplete: function () {
          input.classList.remove('phone-error');
          removePhoneErrorMessage(input);
        },
        onincomplete: function () {
          input.classList.add('phone-error');
          showPhoneErrorMessage(input, 'Введите корректный мобильный номер (начинается с 9)');
        }
      }).mask(input);
    });
  }

  function showPhoneErrorMessage(input, message) {
    let errorDiv = input.parentNode.querySelector('.phone-error-message');
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'phone-error-message';
      errorDiv.style.color = 'red';
      errorDiv.style.fontSize = '12px';
      errorDiv.style.marginTop = '4px';
      input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    errorDiv.textContent = message;
  }

  function removePhoneErrorMessage(input) {
    const errorDiv = input.parentNode.querySelector('.phone-error-message');
    if (errorDiv) errorDiv.remove();
  }

  function normalizePhone(phone) {
    if (!phone) return null;
    let digits = phone.replace(/\D/g, '');
    if (digits.startsWith('8')) digits = '7' + digits.slice(1);
    if (digits.length === 10) digits = '7' + digits;
    if (digits.length === 11 && digits.startsWith('7')) return '+' + digits;
    return null; // невалидный номер
  }

  // Вызываем инициализацию масок
  initPhoneMasks();

  const navToggle = document.querySelector(".nav-toggle");
  const navPanel = document.querySelector(".site-header__nav");
  if (navToggle && navPanel) {
    navToggle.addEventListener("click", () => {
      const open = navPanel.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    navPanel.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        navPanel.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  function openModal(id) {
    const d = document.getElementById(id);
    if (d && typeof d.showModal === "function") d.showModal();
  }

  function closeModal(dialog) {
    if (dialog && typeof dialog.close === "function") dialog.close();
  }

  document.querySelectorAll('[data-open-modal="short"]').forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openModal("modal-short");
    });
  });

  document.querySelectorAll('[data-open-modal="long"]').forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openModal("modal-long");
    });
  });

  document.querySelectorAll("[data-open-privacy]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openModal("modal-privacy");
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      closeModal(btn.closest("dialog"));
    });
  });

  ["modal-short", "modal-long", "modal-privacy"].forEach((id) => {
    const d = document.getElementById(id);
    d?.addEventListener("click", (e) => {
      if (e.target === d) d.close();
    });
  });

  const slider = document.querySelector(".cases-slider");
  const viewport = slider?.querySelector(".cases-slider__viewport");
  const track = slider?.querySelector(".cases-slider__track");
  const prevBtn = slider?.querySelector(".cases-slider__nav--prev");
  const nextBtn = slider?.querySelector(".cases-slider__nav--next");
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (slider && viewport && track) {
    const baseSlides = Array.from(track.children);
    const gapPx = () => parseFloat(window.getComputedStyle(track).gap || "0") || 0;
    let perView = 3;
    let logicalIndex = 0;
    let currentIndex = 0;
    let cardStep = 0;
    let isAnimating = false;
    let swipeStartX = 0;
    let swipeStartY = 0;
    let swipeDeltaX = 0;
    let didDrag = false;
    let animationFallbackTimer = null;

    function resolvePerView() {
      if (window.innerWidth <= 700) return 1;
      if (window.innerWidth <= 1100) return 2;
      return 3;
    }

    function setTrackPosition(useTransition) {
      const duration = prefersReducedMotion ? "0ms" : "";
      track.style.transitionDuration = duration;
      track.style.transitionProperty = useTransition ? "transform" : "none";
      const renderedSlides = track.children;
      const activeSlide = renderedSlides[currentIndex];
      if (!activeSlide) return;
      const viewportCenter = viewport.clientWidth / 2;
      const slideCenter = activeSlide.offsetLeft + activeSlide.offsetWidth / 2;
      track.style.transform = "translateX(" + (viewportCenter - slideCenter) + "px)";
    }

    function updateCardStates() {
      const renderedSlides = Array.from(track.children);
      if (!renderedSlides.length) return;
      renderedSlides.forEach((slide, idx) => {
        slide.classList.remove("is-active", "is-near");
        const distance = Math.abs(idx - currentIndex);
        if (distance === 0) {
          slide.classList.add("is-active");
        } else if (distance === 1) {
          slide.classList.add("is-near");
        }
      });
    }

    function rebuild() {
      if (!baseSlides.length) return;
      perView = Math.min(resolvePerView(), baseSlides.length);
      const safePerView = Math.max(1, perView);
      track.innerHTML = "";

      const startClones = baseSlides.slice(-safePerView).map((card) => card.cloneNode(true));
      const endClones = baseSlides.slice(0, safePerView).map((card) => card.cloneNode(true));

      startClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        track.appendChild(clone);
      });
      baseSlides.forEach((card) => track.appendChild(card));
      endClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        track.appendChild(clone);
      });

      const firstCard = track.querySelector(".case-card");
      cardStep = firstCard ? firstCard.getBoundingClientRect().width + gapPx() : 0;
      logicalIndex = ((logicalIndex % baseSlides.length) + baseSlides.length) % baseSlides.length;
      currentIndex = safePerView + logicalIndex;
      setTrackPosition(false);
      updateCardStates();
    }

    function moveBy(delta) {
      if (isAnimating || !cardStep) return;
      isAnimating = true;
      logicalIndex = (logicalIndex + delta + baseSlides.length) % baseSlides.length;
      currentIndex += delta;
      setTrackPosition(true);
      updateCardStates();

      clearTimeout(animationFallbackTimer);
      const transitionDurationMs = prefersReducedMotion
        ? 20
        : parseFloat(window.getComputedStyle(track).transitionDuration || "0.4") * 1000;
      animationFallbackTimer = setTimeout(() => {
        finishTransition();
      }, transitionDurationMs + 120);
    }

    function finishTransition() {
      if (!isAnimating) return;
      clearTimeout(animationFallbackTimer);
      animationFallbackTimer = null;
      if (!baseSlides.length) {
        isAnimating = false;
        return;
      }
      const safePerView = Math.max(1, perView);
      let jumped = false;
      if (currentIndex < safePerView) {
        currentIndex += baseSlides.length;
        jumped = true;
      } else if (currentIndex >= safePerView + baseSlides.length) {
        currentIndex -= baseSlides.length;
        jumped = true;
      }
      if (jumped) {
        slider.classList.add("is-resetting");
        const prevDuration = track.style.transitionDuration;
        track.style.transitionDuration = "0ms";
        setTrackPosition(false);
        void track.offsetHeight;
        track.style.transitionDuration = prevDuration;
        requestAnimationFrame(() => {
          slider.classList.remove("is-resetting");
        });
      }
      updateCardStates();
      isAnimating = false;
    }

    track.addEventListener("transitionend", (e) => {
      if (e.target !== track || e.propertyName !== "transform") return;
      finishTransition();
    });

    prevBtn?.addEventListener("click", () => moveBy(-1));
    nextBtn?.addEventListener("click", () => moveBy(1));

    track.addEventListener("keydown", (e) => {
      const card = e.target.closest(".case-card");
      if (!card || card.getAttribute("aria-hidden") === "true") return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        moveBy(1);
      }
    });

    viewport.addEventListener(
      "pointerdown",
      (e) => {
        swipeStartX = e.clientX;
        swipeStartY = e.clientY;
        swipeDeltaX = 0;
        didDrag = false;
      },
      { passive: true }
    );

    viewport.addEventListener(
      "pointermove",
      (e) => {
        swipeDeltaX = e.clientX - swipeStartX;
        if (Math.abs(swipeDeltaX) > 6) didDrag = true;
      },
      { passive: true }
    );

    viewport.addEventListener("pointerup", (e) => {
      const deltaX = e.clientX - swipeStartX;
      const deltaY = e.clientY - swipeStartY;
      if (Math.abs(deltaY) > Math.abs(deltaX)) return;
      const threshold = Math.max(42, cardStep * 0.18);
      if (deltaX <= -threshold || swipeDeltaX <= -threshold) {
        moveBy(1);
      } else if (deltaX >= threshold || swipeDeltaX >= threshold) {
        moveBy(-1);
      }
    });

    viewport.addEventListener("click", (e) => {
      const card = e.target.closest(".case-card");
      if (!card) return;
      if (didDrag) {
        didDrag = false;
        return;
      }
      const clickedIndex = Array.from(track.children).indexOf(card);
      if (clickedIndex < currentIndex) {
        moveBy(-1);
        return;
      }
      moveBy(1);
    });

    let resizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        rebuild();
        isAnimating = false;
      }, 120);
    });

    rebuild();
    updateCardStates();
  }

  const licensesSlider = document.querySelector(".licenses-slider");
  const licensesViewport = licensesSlider?.querySelector(".licenses-slider__viewport");
  const licensesTrack = licensesSlider?.querySelector(".licenses-slider__track");
  const licensesPrevBtn = licensesSlider?.querySelector(".licenses-slider__nav--prev");
  const licensesNextBtn = licensesSlider?.querySelector(".licenses-slider__nav--next");

  if (licensesSlider && licensesViewport && licensesTrack) {
    const baseSlides = Array.from(licensesTrack.children);
    const gapPx = () => parseFloat(window.getComputedStyle(licensesTrack).gap || "0") || 0;
    let perView = 5;
    let logicalIndex = 0;
    let currentIndex = 0;
    let slideStep = 0;
    let isAnimating = false;
    let swipeStartX = 0;
    let swipeStartY = 0;
    let swipeDeltaX = 0;
    let didDrag = false;
    let animationFallbackTimer = null;

    function resolvePerView() {
      if (window.innerWidth <= 700) return 1;
      if (window.innerWidth <= 1100) return 3;
      return 5;
    }

    function setTrackPosition(useTransition) {
      const duration = prefersReducedMotion ? "0ms" : "";
      licensesTrack.style.transitionDuration = duration;
      licensesTrack.style.transitionProperty = useTransition ? "transform" : "none";
      const renderedSlides = licensesTrack.children;
      const activeSlide = renderedSlides[currentIndex];
      if (!activeSlide) return;
      const viewportCenter = licensesViewport.clientWidth / 2;
      const slideCenter = activeSlide.offsetLeft + activeSlide.offsetWidth / 2;
      licensesTrack.style.transform = "translateX(" + (viewportCenter - slideCenter) + "px)";
    }

    function updateCardStates() {
      const renderedSlides = Array.from(licensesTrack.children);
      if (!renderedSlides.length) return;
      renderedSlides.forEach((slide, idx) => {
        slide.classList.remove("is-active", "is-near");
        const distance = Math.abs(idx - currentIndex);
        if (distance === 0) {
          slide.classList.add("is-active");
        } else if (distance === 1) {
          slide.classList.add("is-near");
        }
      });
    }

    function rebuild() {
      if (!baseSlides.length) return;
      perView = Math.min(resolvePerView(), baseSlides.length);
      const safePerView = Math.max(1, perView);
      licensesTrack.innerHTML = "";

      const startClones = baseSlides.slice(-safePerView).map((card) => card.cloneNode(true));
      const endClones = baseSlides.slice(0, safePerView).map((card) => card.cloneNode(true));

      startClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        licensesTrack.appendChild(clone);
      });
      baseSlides.forEach((card) => licensesTrack.appendChild(card));
      endClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        licensesTrack.appendChild(clone);
      });

      const firstCard = licensesTrack.querySelector(".license-thumb");
      slideStep = firstCard ? firstCard.getBoundingClientRect().width + gapPx() : 0;
      logicalIndex = ((logicalIndex % baseSlides.length) + baseSlides.length) % baseSlides.length;
      currentIndex = safePerView + logicalIndex;
      setTrackPosition(false);
      updateCardStates();
    }

    function moveBy(delta) {
      if (isAnimating || !slideStep) return;
      isAnimating = true;
      logicalIndex = (logicalIndex + delta + baseSlides.length) % baseSlides.length;
      currentIndex += delta;
      setTrackPosition(true);
      updateCardStates();

      clearTimeout(animationFallbackTimer);
      const transitionDurationMs = prefersReducedMotion
        ? 20
        : parseFloat(window.getComputedStyle(licensesTrack).transitionDuration || "0.4") * 1000;
      animationFallbackTimer = setTimeout(() => {
        finishTransition();
      }, transitionDurationMs + 120);
    }

    function finishTransition() {
      if (!isAnimating) return;
      clearTimeout(animationFallbackTimer);
      animationFallbackTimer = null;
      if (!baseSlides.length) {
        isAnimating = false;
        return;
      }
      const safePerView = Math.max(1, perView);
      let jumped = false;
      if (currentIndex < safePerView) {
        currentIndex += baseSlides.length;
        jumped = true;
      } else if (currentIndex >= safePerView + baseSlides.length) {
        currentIndex -= baseSlides.length;
        jumped = true;
      }
      if (jumped) {
        const prevDuration = licensesTrack.style.transitionDuration;
        licensesTrack.style.transitionDuration = "0ms";
        setTrackPosition(false);
        void licensesTrack.offsetHeight;
        licensesTrack.style.transitionDuration = prevDuration;
      }
      updateCardStates();
      isAnimating = false;
    }

    licensesTrack.addEventListener("transitionend", (e) => {
      if (e.target !== licensesTrack || e.propertyName !== "transform") return;
      finishTransition();
    });

    licensesPrevBtn?.addEventListener("click", () => moveBy(-1));
    licensesNextBtn?.addEventListener("click", () => moveBy(1));

    licensesViewport.addEventListener(
      "pointerdown",
      (e) => {
        swipeStartX = e.clientX;
        swipeStartY = e.clientY;
        swipeDeltaX = 0;
        didDrag = false;
      },
      { passive: true }
    );

    licensesViewport.addEventListener(
      "pointermove",
      (e) => {
        swipeDeltaX = e.clientX - swipeStartX;
        if (Math.abs(swipeDeltaX) > 6) didDrag = true;
      },
      { passive: true }
    );

    licensesViewport.addEventListener("pointerup", (e) => {
      const deltaX = e.clientX - swipeStartX;
      const deltaY = e.clientY - swipeStartY;
      if (Math.abs(deltaY) > Math.abs(deltaX)) return;
      const threshold = Math.max(42, slideStep * 0.18);
      if (deltaX <= -threshold || swipeDeltaX <= -threshold) {
        moveBy(1);
      } else if (deltaX >= threshold || swipeDeltaX >= threshold) {
        moveBy(-1);
      }
    });

    function openLicenseLightbox(thumb) {
      const dlg = document.getElementById("lightbox");
      const img = dlg?.querySelector(".lightbox-dlg__img");
      const src = thumb.getAttribute("data-lightbox-src");
      if (img && src) {
        img.src = src;
        img.alt = thumb.getAttribute("data-lightbox-alt") || "Документ";
        if (typeof dlg?.showModal === "function") dlg.showModal();
      }
    }

    licensesViewport.addEventListener(
      "click",
      (e) => {
        const thumb = e.target.closest(".license-thumb");
        if (!thumb || !licensesViewport.contains(thumb)) return;
        if (didDrag) {
          didDrag = false;
          e.preventDefault();
          e.stopPropagation();
          return;
        }
        const clickedIndex = Array.from(licensesTrack.children).indexOf(thumb);
        if (clickedIndex < 0) return;
        if (clickedIndex === currentIndex) {
          e.preventDefault();
          e.stopPropagation();
          openLicenseLightbox(thumb);
          return;
        }
        e.preventDefault();
        e.stopPropagation();
        if (clickedIndex < currentIndex) {
          moveBy(-1);
        } else {
          moveBy(1);
        }
      },
      true
    );

    let resizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        rebuild();
        isAnimating = false;
      }, 120);
    });

    rebuild();
    updateCardStates();
  }

  const thanksSlider = document.querySelector(".thanks-slider");
  const thanksViewport = thanksSlider?.querySelector(".thanks-slider__viewport");
  const thanksTrack = thanksSlider?.querySelector(".thanks-slider__track");
  const thanksPrevBtn = thanksSlider?.querySelector(".thanks-slider__nav--prev");
  const thanksNextBtn = thanksSlider?.querySelector(".thanks-slider__nav--next");

  if (thanksSlider && thanksViewport && thanksTrack) {
    const baseSlides = Array.from(thanksTrack.children);
    const gapPx = () => parseFloat(window.getComputedStyle(thanksTrack).gap || "0") || 0;
    let perView = 5;
    let logicalIndex = 0;
    let currentIndex = 0;
    let slideStep = 0;
    let isAnimating = false;
    let swipeStartX = 0;
    let swipeStartY = 0;
    let swipeDeltaX = 0;
    let didDrag = false;
    let animationFallbackTimer = null;

    function resolvePerView() {
      if (window.innerWidth <= 700) return 1;
      if (window.innerWidth <= 1100) return 3;
      return 5;
    }

    function setTrackPosition(useTransition) {
      const duration = prefersReducedMotion ? "0ms" : "";
      thanksTrack.style.transitionDuration = duration;
      thanksTrack.style.transitionProperty = useTransition ? "transform" : "none";
      const renderedSlides = thanksTrack.children;
      const activeSlide = renderedSlides[currentIndex];
      if (!activeSlide) return;
      const viewportCenter = thanksViewport.clientWidth / 2;
      const slideCenter = activeSlide.offsetLeft + activeSlide.offsetWidth / 2;
      thanksTrack.style.transform = "translateX(" + (viewportCenter - slideCenter) + "px)";
    }

    function updateCardStates() {
      const renderedSlides = Array.from(thanksTrack.children);
      if (!renderedSlides.length) return;
      renderedSlides.forEach((slide, idx) => {
        slide.classList.remove("is-active", "is-near");
        const distance = Math.abs(idx - currentIndex);
        if (distance === 0) {
          slide.classList.add("is-active");
        } else if (distance === 1) {
          slide.classList.add("is-near");
        }
      });
    }

    function rebuild() {
      if (!baseSlides.length) return;
      perView = Math.min(resolvePerView(), baseSlides.length);
      const safePerView = Math.max(1, perView);
      thanksTrack.innerHTML = "";

      const startClones = baseSlides.slice(-safePerView).map((card) => card.cloneNode(true));
      const endClones = baseSlides.slice(0, safePerView).map((card) => card.cloneNode(true));

      startClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        thanksTrack.appendChild(clone);
      });
      baseSlides.forEach((card) => thanksTrack.appendChild(card));
      endClones.forEach((clone) => {
        clone.setAttribute("aria-hidden", "true");
        clone.tabIndex = -1;
        thanksTrack.appendChild(clone);
      });

      const firstCard = thanksTrack.querySelector(".thanks-thumb");
      slideStep = firstCard ? firstCard.getBoundingClientRect().width + gapPx() : 0;
      logicalIndex = ((logicalIndex % baseSlides.length) + baseSlides.length) % baseSlides.length;
      currentIndex = safePerView + logicalIndex;
      setTrackPosition(false);
      updateCardStates();
    }

    function moveBy(delta) {
      if (isAnimating || !slideStep) return;
      isAnimating = true;
      logicalIndex = (logicalIndex + delta + baseSlides.length) % baseSlides.length;
      currentIndex += delta;
      setTrackPosition(true);
      updateCardStates();

      clearTimeout(animationFallbackTimer);
      const transitionDurationMs = prefersReducedMotion
        ? 20
        : parseFloat(window.getComputedStyle(thanksTrack).transitionDuration || "0.4") * 1000;
      animationFallbackTimer = setTimeout(() => {
        finishTransition();
      }, transitionDurationMs + 120);
    }

    function finishTransition() {
      if (!isAnimating) return;
      clearTimeout(animationFallbackTimer);
      animationFallbackTimer = null;
      if (!baseSlides.length) {
        isAnimating = false;
        return;
      }
      const safePerView = Math.max(1, perView);
      let jumped = false;
      if (currentIndex < safePerView) {
        currentIndex += baseSlides.length;
        jumped = true;
      } else if (currentIndex >= safePerView + baseSlides.length) {
        currentIndex -= baseSlides.length;
        jumped = true;
      }
      if (jumped) {
        const prevDuration = thanksTrack.style.transitionDuration;
        thanksTrack.style.transitionDuration = "0ms";
        setTrackPosition(false);
        void thanksTrack.offsetHeight;
        thanksTrack.style.transitionDuration = prevDuration;
      }
      updateCardStates();
      isAnimating = false;
    }

    thanksTrack.addEventListener("transitionend", (e) => {
      if (e.target !== thanksTrack || e.propertyName !== "transform") return;
      finishTransition();
    });

    thanksPrevBtn?.addEventListener("click", () => moveBy(-1));
    thanksNextBtn?.addEventListener("click", () => moveBy(1));

    thanksViewport.addEventListener(
      "pointerdown",
      (e) => {
        swipeStartX = e.clientX;
        swipeStartY = e.clientY;
        swipeDeltaX = 0;
        didDrag = false;
      },
      { passive: true }
    );

    thanksViewport.addEventListener(
      "pointermove",
      (e) => {
        swipeDeltaX = e.clientX - swipeStartX;
        if (Math.abs(swipeDeltaX) > 6) didDrag = true;
      },
      { passive: true }
    );

    thanksViewport.addEventListener("pointerup", (e) => {
      const deltaX = e.clientX - swipeStartX;
      const deltaY = e.clientY - swipeStartY;
      if (Math.abs(deltaY) > Math.abs(deltaX)) return;
      const threshold = Math.max(42, slideStep * 0.18);
      if (deltaX <= -threshold || swipeDeltaX <= -threshold) {
        moveBy(1);
      } else if (deltaX >= threshold || swipeDeltaX >= threshold) {
        moveBy(-1);
      }
    });

    function openThanksLightbox(thumb) {
      const dlg = document.getElementById("lightbox");
      const img = dlg?.querySelector(".lightbox-dlg__img");
      const src = thumb.getAttribute("data-lightbox-src");
      if (img && src) {
        img.src = src;
        img.alt = thumb.getAttribute("data-lightbox-alt") || "Документ";
        if (typeof dlg?.showModal === "function") dlg.showModal();
      }
    }

    thanksViewport.addEventListener(
      "click",
      (e) => {
        const thumb = e.target.closest(".thanks-thumb");
        if (!thumb || !thanksViewport.contains(thumb)) return;
        if (didDrag) {
          didDrag = false;
          e.preventDefault();
          e.stopPropagation();
          return;
        }
        const clickedIndex = Array.from(thanksTrack.children).indexOf(thumb);
        if (clickedIndex < 0) return;
        if (clickedIndex === currentIndex) {
          e.preventDefault();
          e.stopPropagation();
          openThanksLightbox(thumb);
          return;
        }
        e.preventDefault();
        e.stopPropagation();
        if (clickedIndex < currentIndex) {
          moveBy(-1);
        } else {
          moveBy(1);
        }
      },
      true
    );

    let thanksResizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(thanksResizeTimer);
      thanksResizeTimer = setTimeout(() => {
        rebuild();
        isAnimating = false;
      }, 120);
    });

    rebuild();
    updateCardStates();
  }

  const lightbox = document.getElementById("lightbox");
  const lightboxImg = lightbox?.querySelector(".lightbox-dlg__img");
  document.querySelectorAll("[data-lightbox-src]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const src = btn.getAttribute("data-lightbox-src");
      if (lightboxImg && src) {
        lightboxImg.src = src;
        lightboxImg.alt = btn.getAttribute("data-lightbox-alt") || "Документ";
        lightbox?.showModal();
      }
    });
  });
  lightbox?.querySelector("[data-close-lightbox]")?.addEventListener("click", () => {
    lightbox.close();
  });
  lightbox?.addEventListener("click", (e) => {
    const t = e.target;
    if (t.classList.contains("lightbox-dlg__inner") || t === lightbox) {
      lightbox.close();
    }
  });
  lightboxImg?.addEventListener("click", (e) => e.stopPropagation());

  if (window.matchMedia("(hover: none)").matches) {
    document.querySelectorAll(".bento-card").forEach((card) => {
      card.addEventListener("click", () => {
        card.classList.toggle("is-expanded");
      });
    });
  }

  // ---- Обработка отправки форм ----
  const forms = document.querySelectorAll('form[data-form="lead"], #footer-lead-form');
  forms.forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const submitBtn = form.querySelector('button[type="submit"]');
      const agreeCheck = form.querySelector('[name="agree"]');

      if (agreeCheck && !agreeCheck.checked) {
        alert("Пожалуйста, подтвердите согласие с политикой конфиденциальности");
        return;
      }

      const isLarge = !!form.querySelector('[name="name"]');
      const formData = new FormData(form);
      const rawPhone = formData.get("phone");
      const phone = normalizePhone(rawPhone);

      if (!phone) {
        const phoneInput = form.querySelector('[type="tel"]');
        if (phoneInput) {
          phoneInput.classList.add('phone-error');
          showPhoneErrorMessage(phoneInput, 'Введите полный номер телефона (10 цифр)');
        }
        return;
      }

      const submitData = {
        phone: phone,
        form_type: isLarge ? "large" : "small",
      };

      if (isLarge) {
        submitData.name = formData.get("name") || "";
        submitData.email = formData.get("email") || "";
        submitData.comment = formData.get("comment") || "";

        const fileInput = form.querySelector('input[type="file"]');
        if (fileInput && fileInput.files && fileInput.files[0]) {
          try {
            if (submitBtn) submitBtn.disabled = true;
            const originalText = submitBtn ? submitBtn.textContent : "";
            if (submitBtn) submitBtn.textContent = "Загрузка файла...";

            submitData.file_uuid = await uploadFile(fileInput.files[0]);

            if (submitBtn) submitBtn.textContent = originalText;
          } catch (err) {
            alert("Ошибка при загрузке файла: " + err.message);
            if (submitBtn) submitBtn.disabled = false;
            return;
          }
        } else {
          submitData.file_uuid = null;
        }
      }

      try {
        if (submitBtn) submitBtn.disabled = true;
        const result = await submitLead(submitData);

        alert("Заявка успешно отправлена!");

        if (typeof ym !== 'undefined') {
          if (submitData.form_type === 'small') {
            ym(108573733, 'reachGoal', 'form_small');
          } else if (submitData.form_type === 'large') {
            ym(108573733, 'reachGoal', 'form_large');
          }
          ym(108573733, 'reachGoal', 'zayavka');
        }

        form.reset();

        // Сброс визуального состояния файла (если есть)
        const dropZone = form.querySelector(".modal-dlg__drop");
        if (dropZone) {
          dropZone.classList.remove("has-file");
          const fileLabel = dropZone.querySelector(".modal-dlg__drop-file");
          if (fileLabel) fileLabel.textContent = "";
        }

        // Закрытие модалки
        const dialog = form.closest("dialog");
        if (dialog) dialog.close();

      } catch (err) {
        alert("Ошибка при отправке заявки: " + err.message);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  });

  const fileInput = document.getElementById("modal-long-file");
  const dropZone = document.querySelector(".modal-dlg__drop");
  if (fileInput && dropZone) {
    const fileLabel = dropZone.querySelector(".modal-dlg__drop-file");
    const syncFileState = () => {
      const selected = fileInput.files && fileInput.files[0];
      if (!selected) {
        dropZone.classList.remove("has-file");
        if (fileLabel) fileLabel.textContent = "";
        return;
      }
      dropZone.classList.add("has-file");
      if (fileLabel) fileLabel.textContent = selected.name;
    };

    fileInput.addEventListener("change", syncFileState);
    syncFileState();
  }

  (function initScrollReveal() {
    const nodes = document.querySelectorAll(".reveal-on-scroll");
    if (!nodes.length) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      nodes.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        });
      },
      { root: null, rootMargin: "0px 0px -8% 0px", threshold: 0.06 }
    );
    nodes.forEach((el) => io.observe(el));
  })();
  // ---- Вспомогательные функции API ----
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(errText || "Ошибка загрузки файла");
    }
    const data = await response.json();
    return data.file_uuid;
  }

  async function submitLead(data) {
    const response = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.message || "Ошибка отправки заявки");
    }
    return await response.json();
  }
})();
