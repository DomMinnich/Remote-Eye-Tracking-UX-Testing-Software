// script.js - Updated for Light Theme Redesign

/*
      CONTENTS OF THIS FILE
 NavMenu Logic             | ~Line 10-65   - Updated Selectors
 Clock/Date (Keep if used) | ~Line 68-94   - No changes usually needed
 Removed old home/auth JS  | N/A
*/

// --- Navigation Menu Logic ---
document.addEventListener('DOMContentLoaded', () => {
  const mobileToggle = document.querySelector('.nav-mobile-toggle');
  const mobileMenu = document.querySelector('.nav-mobile-menu');
  const mobileClose = document.querySelector('.nav-mobile-menu__close');
  const navOverlay = document.querySelector('.nav-overlay');
  const expandableItems = document.querySelectorAll('.nav-mobile__item--expandable > a'); // Target the link inside

  // Function to open the mobile menu
  function openMenu() {
      if (!mobileMenu || !navOverlay || !mobileToggle) return;
      mobileMenu.classList.add('active');
      navOverlay.classList.add('active');
      mobileToggle.setAttribute('aria-expanded', 'true');
      mobileToggle.classList.add('active'); // Optional: For toggle animation
      document.body.style.overflow = 'hidden'; // Prevent background scroll
  }

  // Function to close the mobile menu
  function closeMenu() {
      if (!mobileMenu || !navOverlay || !mobileToggle) return;
      mobileMenu.classList.remove('active');
      navOverlay.classList.remove('active');
      mobileToggle.setAttribute('aria-expanded', 'false');
       mobileToggle.classList.remove('active'); // Optional: For toggle animation
      // Close all open submenus when closing main menu
      document.querySelectorAll('.nav-mobile__item--expandable.active').forEach(item => {
          item.classList.remove('active');
          const submenu = item.querySelector('.nav-mobile__submenu');
          if (submenu) submenu.style.maxHeight = null;
      });
      document.body.style.overflow = ''; // Restore scroll
  }

  // Event listeners for menu toggle, close button, and overlay
  if (mobileToggle) {
      mobileToggle.addEventListener('click', () => {
          if (mobileMenu?.classList.contains('active')) {
              closeMenu();
          } else {
              openMenu();
          }
      });
  }
  if (mobileClose) {
      mobileClose.addEventListener('click', closeMenu);
  }
  if (navOverlay) {
      navOverlay.addEventListener('click', closeMenu);
  }

  // Event listeners for expanding/collapsing mobile submenus
  expandableItems.forEach(link => {
      link.addEventListener('click', (e) => {
          e.preventDefault(); // Prevent link navigation for the parent item
          const parentItem = link.closest('.nav-mobile__item--expandable'); // Get the parent LI
          const submenu = parentItem?.querySelector('.nav-mobile__submenu');

          if (!parentItem || !submenu) return;

          if (parentItem.classList.contains('active')) {
              // Collapse current submenu
              parentItem.classList.remove('active');
              submenu.style.maxHeight = null;
          } else {
              // Collapse any other open submenus first
              document.querySelectorAll('.nav-mobile__item--expandable.active').forEach(openItem => {
                  if (openItem !== parentItem) {
                      openItem.classList.remove('active');
                      const openSubmenu = openItem.querySelector('.nav-mobile__submenu');
                      if (openSubmenu) openSubmenu.style.maxHeight = null;
                  }
              });
              // Expand the clicked submenu
              parentItem.classList.add('active');
              submenu.style.maxHeight = submenu.scrollHeight + "px"; // Expand to content height
          }
      });
  });

  // Prevent submenu links themselves from triggering collapse (if event bubbles up)
  const submenuLinks = document.querySelectorAll('.nav-mobile__submenu a');
  submenuLinks.forEach(link => {
      link.addEventListener('click', (e) => {
          e.stopPropagation(); // Stop click from reaching parent item listener
      });
  });

}); // End DOMContentLoaded for Nav

// --- Clock and Date Update ---
// (Keep this if used on home page or elsewhere)
function updateClockAndDate() {
  const clockElement = document.getElementById("clock"); // Assumes ID="clock" exists
  const dateElement = document.getElementById("date"); // Assumes ID="date" exists

  if (!clockElement && !dateElement) {
      // No clock/date elements found on this page, do nothing
      // console.log("No clock/date elements to update."); // Optional debug
      return;
  }

  const now = new Date();

  // Time (e.g., 1:35 PM)
  const timeString = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });

  // Date (e.g., October 26, 2023)
  const dateString = now.toLocaleDateString([], { year: 'numeric', month: 'long', day: 'numeric' });

  if (clockElement) clockElement.textContent = timeString;
  if (dateElement) dateElement.textContent = dateString;
}

// Update clock/date every 10 seconds and immediately on load
setInterval(updateClockAndDate, 10000);
document.addEventListener('DOMContentLoaded', updateClockAndDate);
