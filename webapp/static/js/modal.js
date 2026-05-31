/**
 * Modal management module for Shovo
 */

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(',');

let lastActiveElement = null;

function getFocusableElements(modal) {
  return Array.from(modal.querySelectorAll(focusableSelector))
    .filter((element) => element.offsetParent !== null || element === document.activeElement);
}

function focusModal(modal) {
  const focusable = getFocusableElements(modal);
  const target = focusable[0] || modal;
  if (!modal.hasAttribute('tabindex')) {
    modal.setAttribute('tabindex', '-1');
  }
  requestAnimationFrame(() => target.focus({ preventScroll: true }));
}

/**
 * Open a modal
 * @param {HTMLElement} modal - Modal element
 */
export function openModal(modal) {
  if (!modal) return;
  lastActiveElement = document.activeElement instanceof HTMLElement ? document.activeElement : lastActiveElement;
  modal.classList.add('is-visible');
  modal.setAttribute('aria-hidden', 'false');
  if (modal.getAttribute('role') === 'dialog') {
    focusModal(modal);
  }
}

/**
 * Close a modal
 * @param {HTMLElement} modal - Modal element
 */
export function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('is-visible');
  modal.setAttribute('aria-hidden', 'true');
  if (modal.getAttribute('role') === 'dialog' && lastActiveElement?.isConnected) {
    lastActiveElement.focus({ preventScroll: true });
  }
}

/**
 * Check if a modal is open
 * @param {HTMLElement} modal - Modal element
 * @returns {boolean}
 */
export function isModalOpen(modal) {
  return modal?.classList.contains('is-visible') || false;
}

/**
 * Get large image URL from thumbnail
 * @param {string} url - Thumbnail URL
 * @returns {string} - Large image URL
 */
export function getLargeImage(url) {
  if (!url) {
    return 'https://via.placeholder.com/500x750?text=No+Image';
  }
  if (url.includes('._V1_')) {
    return url.replace(/_UX\d+_CR0,0,\d+,\d+_AL_/i, '_UX500_CR0,0,500,750_AL_');
  }
  return url;
}

/**
 * Create modal handlers for a specific modal
 * @param {HTMLElement} modal - Modal element
 * @param {HTMLElement} closeButton - Close button element
 * @returns {object} - Handler functions
 */
export function createModalHandlers(modal, closeButton) {
  const open = () => openModal(modal);
  const close = () => closeModal(modal);

  // Close on button click
  if (closeButton) {
    closeButton.addEventListener('click', close);
  }

  // Close on backdrop click
  if (modal) {
    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        close();
      }
    });
  }

  return { open, close, isOpen: () => isModalOpen(modal) };
}

/**
 * Setup escape key handler for modals
 * @param {object} modals - Object mapping names to modal elements
 * @param {object} handlers - Object mapping names to close handlers
 */
export function setupEscapeHandler(modals, handlers) {
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Tab') {
      const openDialog = Object.values(modals).find((modal) => modal?.getAttribute('role') === 'dialog' && isModalOpen(modal));
      if (!openDialog) return;
      const focusable = getFocusableElements(openDialog);
      if (!focusable.length) {
        event.preventDefault();
        openDialog.focus({ preventScroll: true });
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus({ preventScroll: true });
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus({ preventScroll: true });
      }
      return;
    }

    if (event.key !== 'Escape') return;

    for (const [name, modal] of Object.entries(modals)) {
      if (isModalOpen(modal) && handlers[name]) {
        handlers[name]();
        break;
      }
    }
  });
}
