/**
 * Mobile enhancements module for Shovo
 */

let loadListCallback = null;

/**
 * Check if device is mobile
 * @returns {boolean}
 */
export function isMobile() {
  return window.matchMedia('(max-width: 768px)').matches;
}

/**
 * Check if device supports touch
 * @returns {boolean}
 */
export function isTouchDevice() {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

/**
 * Attach long-press handlers for card actions
 * @param {HTMLElement} container - Cards container
 * @param {Function} onLongPress - Callback when long press fires
 */
export function attachCardLongPressHandlers(container, onLongPress) {
  if (!container || !isMobile()) return;
  const cards = container.querySelectorAll('.card');
  const pressDelay = 500;
  const moveThreshold = 8;

  cards.forEach((card) => {
    if (card.dataset.longPressSetup) return;
    card.dataset.longPressSetup = 'true';
    let pressTimer = null;
    let startX = 0;
    let startY = 0;
    let pointerId = null;

    const clearPress = () => {
      if (pressTimer) {
        clearTimeout(pressTimer);
        pressTimer = null;
      }
      pointerId = null;
    };

    card.addEventListener('pointerdown', (event) => {
      if (event.pointerType === 'mouse') return;
      pointerId = event.pointerId;
      startX = event.clientX;
      startY = event.clientY;
      pressTimer = setTimeout(() => {
        pressTimer = null;
        if (onLongPress) {
          onLongPress(card);
        }
      }, pressDelay);
    });

    card.addEventListener('pointermove', (event) => {
      if (pointerId !== event.pointerId || !pressTimer) return;
      const deltaX = Math.abs(event.clientX - startX);
      const deltaY = Math.abs(event.clientY - startY);
      if (deltaX > moveThreshold || deltaY > moveThreshold) {
        clearPress();
      }
    });

    card.addEventListener('pointerup', (event) => {
      if (pointerId !== event.pointerId) return;
      clearPress();
    });

    card.addEventListener('pointercancel', (event) => {
      if (pointerId !== event.pointerId) return;
      clearPress();
    });
  });
}

/**
 * Setup mobile-specific event listeners
 */
function setupMobileEventListeners() {
  // Improve modal behavior on mobile
  const modals = document.querySelectorAll('.modal-overlay');
  modals.forEach((modal) => {
    modal.addEventListener(
      'touchmove',
      (e) => {
        if (modal.classList.contains('is-visible')) {
          e.preventDefault();
        }
      },
      { passive: false }
    );
  });
}

/**
 * Setup touch feedback on buttons
 */
function setupTouchFeedback() {
  const buttons = document.querySelectorAll('button, .card-action, .tab, .icon-button');
  buttons.forEach((button) => {
    button.addEventListener(
      'touchstart',
      function () {
        this.classList.add('active-touch');
      },
      { passive: true }
    );

    button.addEventListener(
      'touchend',
      function () {
        this.classList.remove('active-touch');
      },
      { passive: true }
    );

    button.addEventListener(
      'touchcancel',
      function () {
        this.classList.remove('active-touch');
      },
      { passive: true }
    );
  });
}

/**
 * Setup swipe gestures
 */
function setupSwipeGestures() {
  let touchStartX = 0;
  let touchEndX = 0;

  document.addEventListener(
    'touchstart',
    (e) => {
      touchStartX = e.changedTouches[0].screenX;
    },
    { passive: true }
  );

  document.addEventListener(
    'touchend',
    (e) => {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipeGesture(touchStartX, touchEndX);
    },
    { passive: true }
  );
}

/**
 * Handle swipe gesture for tab navigation
 * @param {number} startX - Start X position
 * @param {number} endX - End X position
 */
function handleSwipeGesture(startX, endX) {
  const swipeThreshold = 50;
  const swipeDistance = startX - endX;

  if (Math.abs(swipeDistance) < swipeThreshold) return;

  // Use global variables for tab navigation
  const currentTab = window.mobileActiveTab || 'unwatched';
  const setActiveTab = window.mobileSetActiveTab;

  if (!setActiveTab) return;

  // Swipe left to right (right swipe) - navigate to previous tab
  if (swipeDistance > swipeThreshold) {
    if (currentTab === 'watched') {
      setActiveTab('unwatched');
    }
  }
  // Swipe right to left (left swipe) - navigate to next tab
  else if (swipeDistance < -swipeThreshold) {
    if (currentTab === 'unwatched') {
      setActiveTab('watched');
    }
  }
}

/**
 * Setup swipe gestures for individual cards
 * @param {Function} onRemove - Callback for remove action
 * @param {Function} onToggle - Callback for toggle action
 */
export function setupCardSwipeGestures(onRemove, onToggle) {
  const cards = document.querySelectorAll('.card');

  cards.forEach(card => {
    // Skip setup if already configured
    if (card.dataset.swipeSetup) return;
    card.dataset.swipeSetup = 'true';

    const cardContent = card.querySelector('.card-content');
    const deleteButton = card.querySelector('.card-swipe-delete');
    const moveButton = card.querySelector('.card-swipe-move');

    if (!cardContent || !deleteButton || !moveButton) return;

    let touchStartX = 0;
    let touchStartY = 0;
    let currentTranslateX = 0;
    let isSwiping = false;
    let swipeThreshold = 50;
    let actionThreshold = 100;

    // Update move button icon based on watched status
    const updateMoveButtonIcon = () => {
      const isWatched = card.dataset.watched === '1';
      moveButton.textContent = isWatched ? '↺' : '✓';
      moveButton.setAttribute('aria-label', isWatched ? 'Move to watchlist' : 'Mark watched');
    };

    updateMoveButtonIcon();

    // Delete button touch start handler (prevent card swipe interference)
    deleteButton.addEventListener('touchstart', (e) => {
      e.stopPropagation();
    }, { passive: true });

    // Delete button touch handler
    deleteButton.addEventListener('touchend', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (onRemove) {
        const titleId = card.dataset.titleId;
        onRemove(titleId);
      }
      resetSwipe();
    }, { passive: false });

    // Delete button click handler (fallback for mouse)
    deleteButton.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onRemove) {
        const titleId = card.dataset.titleId;
        onRemove(titleId);
      }
      resetSwipe();
    });

    // Move button touch start handler (prevent card swipe interference)
    moveButton.addEventListener('touchstart', (e) => {
      e.stopPropagation();
    }, { passive: true });

    // Move button touch handler
    moveButton.addEventListener('touchend', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (onToggle) {
        const titleId = card.dataset.titleId;
        const currentWatched = card.dataset.watched === '1';
        onToggle(titleId, !currentWatched);
      }
      resetSwipe();
    }, { passive: false });

    // Move button click handler (fallback for mouse)
    moveButton.addEventListener('click', (e) => {
      e.stopPropagation();
      if (onToggle) {
        const titleId = card.dataset.titleId;
        const currentWatched = card.dataset.watched === '1';
        onToggle(titleId, !currentWatched);
      }
      resetSwipe();
    });

    const resetSwipe = () => {
      cardContent.style.transform = '';
      card.classList.remove('swiping-left', 'swiping-right');
      currentTranslateX = 0;
      isSwiping = false;
    };

    card.addEventListener('touchstart', (e) => {
      // Only handle single touch
      if (e.touches.length !== 1) return;

      // Don't interfere with drag handle
      if (e.target.closest('.card-drag-handle')) return;

      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      isSwiping = false;
      currentTranslateX = 0;
    }, { passive: true });

    card.addEventListener('touchmove', (e) => {
      if (!touchStartX) return;

      const touchCurrentX = e.touches[0].clientX;
      const touchCurrentY = e.touches[0].clientY;
      const deltaX = touchCurrentX - touchStartX;
      const deltaY = touchCurrentY - touchStartY;

      // Only consider horizontal swipes (more horizontal than vertical)
      if (Math.abs(deltaX) < Math.abs(deltaY) || Math.abs(deltaX) < 10) {
        if (!isSwiping) return;
      }

      // Prevent default to avoid scrolling while swiping
      if (isSwiping) {
        e.preventDefault();
      }

      // Start swiping if threshold exceeded
      if (Math.abs(deltaX) > swipeThreshold) {
        isSwiping = true;

        // Limit swipe distance
        const maxSwipe = actionThreshold;
        currentTranslateX = Math.max(-maxSwipe, Math.min(maxSwipe, deltaX));

        cardContent.style.transform = `translateX(${currentTranslateX}px)`;

        // Add visual feedback class
        card.classList.remove('swiping-left', 'swiping-right');
        if (currentTranslateX < -swipeThreshold) {
          card.classList.add('swiping-left');
        } else if (currentTranslateX > swipeThreshold) {
          card.classList.add('swiping-right');
        }
      }
    }, { passive: false });

    card.addEventListener('touchend', (e) => {
      if (!isSwiping) {
        resetSwipe();
        touchStartX = 0;
        touchStartY = 0;
        return;
      }

      // If swiped far enough, keep it revealed, otherwise reset
      if (Math.abs(currentTranslateX) < actionThreshold * 0.6) {
        resetSwipe();
      }

      touchStartX = 0;
      touchStartY = 0;
    }, { passive: true });

    // Reset swipe when clicking elsewhere
    document.addEventListener('click', (e) => {
      if (!card.contains(e.target)) {
        resetSwipe();
      }
    });
  });
}

/**
 * Setup double-tap prevention
 */
function setupDoubleTapPrevention() {
  document.addEventListener('dblclick', (e) => {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
    }
  });
}

/**
 * Setup pull-to-refresh
 */
function setupPullToRefresh() {
  let startY = 0;
  let isPulling = false;
  let pullDistance = 0;
  const pullThreshold = 100;
  const pullElement = document.createElement('div');
  pullElement.className = 'pull-to-refresh';
  pullElement.textContent = '🔄 Pull to refresh';
  pullElement.style.position = 'fixed';
  pullElement.style.top = '-50px';
  pullElement.style.left = '0';
  pullElement.style.width = '100%';
  pullElement.style.textAlign = 'center';
  pullElement.style.padding = '10px';
  pullElement.style.background = 'var(--surface-strong)';
  pullElement.style.color = 'var(--text-soft)';
  pullElement.style.transition = 'top 0.2s ease';
  pullElement.style.zIndex = '1000';
  pullElement.style.fontSize = '0.8rem';
  document.body.appendChild(pullElement);

  document.addEventListener(
    'touchstart',
    (e) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
        isPulling = true;
        pullDistance = 0;
      }
    },
    { passive: true }
  );

  document.addEventListener(
    'touchmove',
    (e) => {
      if (!isPulling) return;
      const currentY = e.touches[0].clientY;
      pullDistance = currentY - startY;

      if (pullDistance > 0) {
        e.preventDefault(); // Prevent scrolling while pulling
        const progress = Math.min(pullDistance / pullThreshold, 1);
        pullElement.textContent = pullDistance >= pullThreshold ? '🔄 Release to refresh' : '🔄 Pull to refresh';
        pullElement.style.top = `${Math.min(pullDistance - 50, 50)}px`;
      }
    },
    { passive: false }
  );

  document.addEventListener('touchend', () => {
    if (isPulling && pullDistance >= pullThreshold && loadListCallback) {
      pullElement.textContent = '🔄 Refreshing...';
      pullElement.style.top = '0';
      setTimeout(() => {
        loadListCallback();
        setTimeout(() => {
          pullElement.style.top = '-50px';
        }, 500);
      }, 300);
    } else {
      pullElement.style.top = '-50px';
    }
    isPulling = false;
  });
}

/**
 * Setup orientation change handler
 */
function setupOrientationHandler() {
  window.addEventListener('orientationchange', () => {
    setTimeout(() => {
      if (loadListCallback) {
        loadListCallback();
      }
    }, 300);
  });
}

/**
 * Setup resize handler
 */
function setupResizeHandler() {
  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      if (isMobile()) {
        document.body.classList.add('is-mobile');
      } else {
        document.body.classList.remove('is-mobile');
      }
    }, 200);
  });
}

/**
 * Initialize mobile enhancements
 * @param {Function} loadList - Callback to reload list
 * @param {Object} options - Additional options
 * @param {Function} options.setActiveTab - Function to set active tab
 * @param {string} options.activeTab - Current active tab
 */
export function setupMobileEnhancements(loadList, options = {}) {
  loadListCallback = loadList;

  if (options.setActiveTab) {
    window.mobileSetActiveTab = options.setActiveTab;
  }
  if (options.activeTab) {
    window.mobileActiveTab = options.activeTab;
  }

  // Only apply mobile enhancements on actual mobile devices (small screens)
  // Don't apply on desktop browsers that happen to support touch events
  if (isMobile()) {
    document.body.classList.add('is-mobile');
    setupTouchFeedback();
    // Removed tab-switching swipe gestures
    // setupSwipeGestures();
    setupDoubleTapPrevention();
    setupPullToRefresh();
    setupMobileEventListeners();

  }

  setupOrientationHandler();
  setupResizeHandler();
}
