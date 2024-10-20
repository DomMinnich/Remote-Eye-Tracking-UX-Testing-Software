//Script for the app

/*
      CONTENTS OF THIS FILE
 NavMenu                  | ~Line 10-56   -Dominic Minnich
 Login/Reg slide-in       | ~Line 60-102   -Dominic Minnich
 .?.?.                    | ~Line ?-?   

 */

// NavMenu A->Z

// Select elements
const menuToggle = document.querySelector(".base-menu-toggle");
const sidebarMenu = document.querySelector(".base-sidebar-menu");
const closeBtn = document.querySelector(".base-close-btn");
const expandableItems = document.querySelectorAll(".base-menu-list > li");

// Set initial max-height for submenus
expandableItems.forEach((item) => {
  const submenu = item.querySelector(".base-submenu");
  if (submenu) {
    submenu.style.maxHeight = "0px"; // Collapse initially
  }
});

// Toggle sidebar visibility with smooth animation
menuToggle.addEventListener("click", () => {
  sidebarMenu.classList.toggle("active");
  menuToggle.classList.toggle("active"); // Rotate bars to "X" shape
});

// Close the sidebar when the close button is clicked
closeBtn.addEventListener("click", () => {
  sidebarMenu.classList.remove("active");
  menuToggle.classList.remove("active"); // Reset menu icon to bars
});

// Expand/Collapse submenus with smooth animation
expandableItems.forEach((item) => {
  item.addEventListener("click", (e) => {
    // Only toggle if the item has a submenu
    const submenu = item.querySelector(".base-submenu");
    if (submenu) {
      e.preventDefault();
      // Toggle the active class for smooth open/close
      item.classList.toggle("active");

      // Toggle max-height dynamically for better smoothness
      if (submenu.style.maxHeight && submenu.style.maxHeight !== "0px") {
        submenu.style.maxHeight = "0px"; // Collapse
      } else {
        submenu.style.maxHeight = submenu.scrollHeight + "px"; // Expand to content height
      }
    }
  });
});


// Login and Register Page Transition
document.addEventListener("DOMContentLoaded", () => {
  // Selecting the login and register page containers
  const loginPage = document.querySelector('.login-page');
  const registerPage = document.querySelector('.register-page');
  
  // Apply the slide-in-from-top effect when the page loads
  if (loginPage) {
    loginPage.classList.add('slideInFromTop');
  }
  
  if (registerPage) {
    registerPage.classList.add('slideInFromTop');
  }

  // Handle the transition from Register to Login
  const loginLink = document.querySelector('.login-link a');
  if (loginLink) {
    loginLink.addEventListener('click', (event) => {
      event.preventDefault(); // Prevent the immediate jump to another page
      if (registerPage) {
        registerPage.classList.add('page-transition'); // Add slide down animation
        setTimeout(() => {
          window.location.href = loginLink.getAttribute('href'); // After animation, navigate
        }, 500); // Delay to allow the animation to complete
      }
    });
  }

  // Handle the transition from Login to Register
  const registerLink = document.querySelector('.register-link a');
  if (registerLink) {
    registerLink.addEventListener('click', (event) => {
      event.preventDefault(); // Prevent the immediate jump to another page
      if (loginPage) {
        loginPage.classList.add('page-transition'); // Add slide down animation
        setTimeout(() => {
          window.location.href = registerLink.getAttribute('href'); // After animation, navigate
        }, 500); // Delay to allow the animation to complete
      }
    });
  }
});


// login and register page transition
document.addEventListener("DOMContentLoaded", () => {
  // Selecting the login and register page containers
  const loginPage = document.querySelector('.login-page');
  const registerPage = document.querySelector('.register-page');

  // Flash messages to detect form errors
  const loginError = document.querySelector('.login-alert');
  const registerError = document.querySelector('.register-alert');
  
  // Apply the slide-in-from-top effect when the page loads
  if (loginPage && !loginError) {
    loginPage.classList.add('slideInFromTop');
  }

  if (registerPage && !registerError) {
    registerPage.classList.add('slideInFromTop');
  }

  // Handle the transition from Register to Login
  const loginLink = document.querySelector('.login-link a');
  if (loginLink) {
    loginLink.addEventListener('click', (event) => {
      event.preventDefault(); // Prevent immediate page jump
      if (registerPage && !registerError) {
        registerPage.classList.add('log-reg-page-transition'); // Add slide down animation
        setTimeout(() => {
          window.location.href = loginLink.getAttribute('href'); // Navigate after animation
        }, 500);
      } else {
        // Directly navigate if there's an error (no animation)
        window.location.href = loginLink.getAttribute('href');
      }
    });
  }

  // Handle the transition from Login to Register
  const registerLink = document.querySelector('.register-link a');
  if (registerLink) {
    registerLink.addEventListener('click', (event) => {
      event.preventDefault(); // Prevent immediate page jump
      if (loginPage && !loginError) {
        loginPage.classList.add('log-reg-page-transition'); // Add slide down animation
        setTimeout(() => {
          window.location.href = registerLink.getAttribute('href'); // Navigate after animation
        }, 500);
      } else {
        // Directly navigate if there's an error (no animation)
        window.location.href = registerLink.getAttribute('href');
      }
    });
  }
});

// .?.?.
