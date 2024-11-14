//Script for the app

/*
      CONTENTS OF THIS FILE
 NavMenu                  | ~Line 10-56   -Dominic Minnich
 Login/Reg slide-in       | ~Line 60-130   -Dominic Minnich
 Home Page                | ~Line 158-252   -Dominic Minnich
 .?.?.                    | ~Line ?-?   

 */

// NavMenu A->Z

// Select elements
const menuToggle = document.querySelector(".base-menu-toggle");
const sidebarMenu = document.querySelector(".base-sidebar-menu");
const closeBtn = document.querySelector(".base-close-btn");
const expandableItems = document.querySelectorAll(".base-menu-list > li");
const dimmingOverlay = document.querySelector(".base-dimming-overlay");

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
  if (sidebarMenu.classList.contains("active")) {
    dimmingOverlay.classList.add("active");
    dimmingOverlay.classList.remove("inactive");
  } else {
    dimmingOverlay.classList.add("inactive");
    dimmingOverlay.classList.remove("active");
  }
});

closeBtn.addEventListener("click", () => {
  sidebarMenu.classList.remove("active");
  menuToggle.classList.remove("active"); // Reset menu icon to bars
  dimmingOverlay.classList.add("inactive");
  dimmingOverlay.classList.remove("active");
});

// Expand/Collapse submenus with smooth animation
expandableItems.forEach((item) => {
  item.addEventListener("click", (e) => {
    // Only toggle if the item has a submenu
    const submenu = item.querySelector(".base-submenu");
    if (submenu && !e.target.closest(".base-submenu a")) {
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

  // Prevent submenu links from closing the submenu
  const links = item.querySelectorAll(".base-submenu a");
  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.stopPropagation();
    });
  });
});

// login and register page transition
document.addEventListener("DOMContentLoaded", () => {
  // Selecting the login and register page containers
  const loginPage = document.querySelector(".login-page");
  const registerPage = document.querySelector(".register-page");
  const loginFlashMessage = document.querySelector(".login-flash-messages");
  const registerFlashMessage = document.querySelector(
    ".register-flash-messages"
  );

  // Function to handle animation based on alert presence
  const handlePageAnimation = (page, flashMessage) => {
    if (flashMessage && flashMessage.children.length > 0) {
      // Alert is present, apply alert animation (0.12s)
      page.classList.add("log-reg-alert-active");
    } else {
      // No alert, apply normal animation (0.8s)
      page.classList.add("slideInFromTop");
    }
  };

  // Apply appropriate animation to the login or register page based on alert presence
  if (loginPage) {
    handlePageAnimation(loginPage, loginFlashMessage);
  }

  if (registerPage) {
    handlePageAnimation(registerPage, registerFlashMessage);
  }

  // Handle the transition from Register to Login
  const loginLink = document.querySelector(".login-link a");
  if (loginLink) {
    loginLink.addEventListener("click", (event) => {
      event.preventDefault(); // Prevent immediate page jump
      if (registerPage) {
        if (registerFlashMessage && registerFlashMessage.children.length > 0) {
          registerPage.classList.add("log-reg-page-transition-alert"); // Add alert transition
        } else {
          registerPage.classList.add("log-reg-page-transition-normal"); // Add normal transition
        }
        setTimeout(
          () => {
            window.location.href = loginLink.getAttribute("href"); // Navigate after animation
          },
          registerFlashMessage && registerFlashMessage.children.length > 0
            ? 120
            : 500
        ); // Timing based on alert
      } else {
        // Directly navigate if there's an error (no animation)
        window.location.href = loginLink.getAttribute("href");
      }
    });
  }

  // Handle the transition from Login to Register
  const registerLink = document.querySelector(".register-link a");
  if (registerLink) {
    registerLink.addEventListener("click", (event) => {
      event.preventDefault(); // Prevent immediate page jump
      if (loginPage) {
        if (loginFlashMessage && loginFlashMessage.children.length > 0) {
          loginPage.classList.add("log-reg-page-transition-alert"); // Add alert transition
        } else {
          loginPage.classList.add("log-reg-page-transition-normal"); // Add normal transition
        }
        setTimeout(
          () => {
            window.location.href = registerLink.getAttribute("href"); // Navigate after animation
          },
          loginFlashMessage && loginFlashMessage.children.length > 0 ? 120 : 500
        ); // Timing based on alert
      } else {
        // Directly navigate if there's an error (no animation)
        window.location.href = registerLink.getAttribute("href");
      }
    });
  }
});

// Home page animations
document.addEventListener("DOMContentLoaded", function () {
  const rainContainer = document.querySelector(".home-raindrops");
  const cards = document.querySelectorAll(".home-card");

  function createRaindrop() {
    const raindrop = document.createElement("div");
    raindrop.classList.add("home-raindrop");
    const leftPosition = Math.random() * 100;
    raindrop.style.left = `${leftPosition}vw`;
    const fallDuration = Math.random() * 2 + 1;
    raindrop.style.animationDuration = `${fallDuration}s`;

    rainContainer.appendChild(raindrop);

    const collisionInterval = setInterval(() => {
      const hitElement = checkCollision(raindrop, cards);
      if (hitElement) {
        createSplashOnElement(raindrop, hitElement);
        clearInterval(collisionInterval);
      }
    }, 20);

    setTimeout(() => {
      if (raindrop.parentNode) {
        createSplashAtBottom(raindrop.style.left);
        raindrop.remove();
      }
    }, fallDuration * 1000);
  }

  function createSplashAtBottom(leftPosition) {
    const splash = document.createElement("div");
    splash.classList.add("home-splash");
    splash.style.left = leftPosition;
    splash.style.bottom = "0";
    rainContainer.appendChild(splash);
    setTimeout(() => {
      splash.remove();
    }, 400);
  }

  function createSplashOnElement(raindrop, element) {
    const raindropRect = raindrop.getBoundingClientRect();
    raindrop.remove();
    const splash = document.createElement("div");
    splash.classList.add("home-splash");
    splash.style.left = `${raindropRect.left}px`;
    splash.style.top = `${raindropRect.top}px`;
    document.body.appendChild(splash);
    setTimeout(() => {
      splash.remove();
    }, 400);
  }

  function checkCollision(raindrop, elements) {
    const raindropRect = raindrop.getBoundingClientRect();
    for (let element of elements) {
      const rect = element.getBoundingClientRect();
      if (
        raindropRect.right > rect.left &&
        raindropRect.left < rect.right &&
        raindropRect.bottom > rect.top &&
        raindropRect.top < rect.bottom
      ) {
        return element;
      }
    }
    return null;
  }

  setInterval(createRaindrop, 150);

  // Trigger bounce animation on cards
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const projectCount = document.getElementById("home-projectCount").innerText;
  const projectTotal = document.getElementById("home-projectTotal").innerText;
  const progressFill = document.getElementById("home-progressFill");

  function updateProgressBar() {
    const count = parseInt(projectCount);
    const total = parseInt(projectTotal);
    const percentage = (count / total) * 100;
    progressFill.style.width = `${percentage}%`;
  }

  updateProgressBar();
});
