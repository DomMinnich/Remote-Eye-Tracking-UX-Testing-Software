//Script for the app

/*
      CONTENTS OF THIS FILE
 NavMenu Base             | ~Line 16-76   -Dominic Minnich
 Login/Reg                | ~Line 79-157   -Dominic Minnich
 Home Page                | ~Line 160-286   -Dominic Minnich
 Video Player             | ~Line 289-468   -Dominic Minnich
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

// Home Page / Dashboard

document.addEventListener("DOMContentLoaded", function () {
  const rainContainer = document.querySelector(".home-raindrops");
  const cards = document.querySelectorAll(".home-card");

  if (rainContainer) {
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
  }

  // Trigger bounce animation on cards
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const projectCount = document.getElementById("home-projectCount");
  const projectTotal = document.getElementById("home-projectTotal");
  const progressFill = document.getElementById("home-progressFill");

  if (projectCount && projectTotal && progressFill) {
    function updateProgressBar() {
      const count = parseInt(projectCount.innerText);
      const total = parseInt(projectTotal.innerText);
      const percentage = (count / total) * 100;
      progressFill.style.width = `${percentage}%`;
    }

    updateProgressBar();
  }
});

// Clock and Date

function updateClockAndDate() {
  const clockElement = document.getElementById("clock");
  const dateElement = document.getElementById("date");

  if (!clockElement || !dateElement) {
    return;
  }

  const now = new Date();
  let hours = now.getHours();
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const seconds = String(now.getSeconds()).padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12;
  const timeString = `${String(hours).padStart(
    2,
    "0"
  )}:${minutes}:${seconds} ${ampm}`;

  const day = String(now.getDate()).padStart(2, "0");
  const month = String(now.getMonth() + 1).padStart(2, "0"); // Months are zero-indexed
  const year = now.getFullYear();
  const dateString = `${day}-${month}-${year}`;

  clockElement.textContent = timeString;
  dateElement.textContent = dateString;
}

// Update clock and date every second
setInterval(updateClockAndDate, 1000);
updateClockAndDate(); // Initial call

// Video Player

document.addEventListener("DOMContentLoaded", function () {
  const tooltipIcon = document.querySelector(".vrs-tooltip-icon");
  const tooltipOverlay = document.querySelector(".vrs-tooltip-overlay");

  tooltipIcon.addEventListener("mouseover", () => {
    tooltipOverlay.style.display = "flex";
  });

  tooltipIcon.addEventListener("mouseout", () => {
    tooltipOverlay.style.display = "none";
  });

  const video = document.getElementById("vrs-video");
  const playPauseBtn = document.getElementById("vrs-play-pause");
  const seekBar = document.getElementById("vrs-seek-bar");
  const timeDisplay = document.getElementById("vrs-time-display");
  const muteBtn = document.getElementById("vrs-mute");
  const volumeBar = document.getElementById("vrs-volume-bar");
  const fullscreenBtn = document.getElementById("vrs-fullscreen");
  const speedControl = document.getElementById("vrs-speed-control");
  const forwardBtn = document.getElementById("vrs-forward");
  const backwardBtn = document.getElementById("vrs-backward");

  // Button functionality
  playPauseBtn.addEventListener("click", () => {
    if (video.paused || video.ended) {
      video.play();
      playPauseBtn.textContent = "❚❚";
    } else {
      video.pause();
      playPauseBtn.textContent = "▶";
    }
  });

  video.addEventListener("click", () => {
    if (video.paused || video.ended) {
      video.play();
      playPauseBtn.textContent = "❚❚";
    } else {
      video.pause();
      playPauseBtn.textContent = "▶";
    }
  });

  forwardBtn.addEventListener("click", () => {
    video.currentTime = Math.min(video.currentTime + 5, video.duration);
  });

  backwardBtn.addEventListener("click", () => {
    video.currentTime = Math.max(video.currentTime - 5, 0);
  });

  video.addEventListener("timeupdate", () => {
    const progress = (video.currentTime / video.duration) * 100;
    seekBar.value = progress;
    timeDisplay.textContent = `${formatTime(video.currentTime)} / ${formatTime(
      video.duration
    )}`;
  });

  seekBar.addEventListener("input", () => {
    const time = (seekBar.value / 100) * video.duration;
    video.currentTime = time;
  });

  muteBtn.addEventListener("click", () => {
    video.muted = !video.muted;
    muteBtn.textContent = video.muted ? "🔇" : "🔈";
  });

  volumeBar.addEventListener("input", () => {
    video.volume = volumeBar.value;
  });

  fullscreenBtn.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      video.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  });

  speedControl.addEventListener("change", () => {
    video.playbackRate = speedControl.value;
  });

  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
  }

  video.addEventListener("loadedmetadata", () => {
    timeDisplay.textContent = `0:00 / ${formatTime(video.duration)}`;
  });

  // Lens functionality
  const lens = document.getElementById("vrs-lens");
  const lensWidth = lens.offsetWidth;
  const lensHeight = lens.offsetHeight;

  let isShiftPressed = false;

  lens.style.display = "none";

  window.addEventListener("keydown", (e) => {
    if (e.key === "Shift") {
      isShiftPressed = true;
      lens.style.display = "block";
      document.body.style.cursor = "none";
    }
  });

  window.addEventListener("keyup", (e) => {
    if (e.key === "Shift") {
      isShiftPressed = false;
      lens.style.display = "none";
      document.body.style.cursor = "auto";
    }
  });

  video.addEventListener("mousemove", moveLens);
  video.addEventListener("touchmove", moveLens);

  function moveLens(e) {
    if (!isShiftPressed) return;

    e.preventDefault();
    const pos = getCursorPos(e);
    let x = pos.x - lensWidth / 2;
    let y = pos.y - lensHeight / 2;

    const videoBounds = video.getBoundingClientRect();
    const maxX = videoBounds.width - lensWidth;
    const maxY = videoBounds.height - lensHeight;

    x = Math.max(0, Math.min(x, maxX));
    y = Math.max(0, Math.min(y, maxY));

    lens.style.left = `${x + videoBounds.left}px`;
    lens.style.top = `${y + videoBounds.top}px`;

    captureAndDisplayFrame(pos);
  }

  function captureAndDisplayFrame(pos) {
    if (!isShiftPressed) return;

    const frame = captureVideoFrame(video);
    lens.style.backgroundImage = `url('${frame}')`;
    lens.style.backgroundSize = `${video.videoWidth * 2}px ${
      video.videoHeight * 2
    }px`;

    const scaleFactorX = video.videoWidth / video.clientWidth;
    const scaleFactorY = video.videoHeight / video.clientHeight;
    const backgroundX = (pos.x * scaleFactorX - lensWidth / 2) * 2;
    const backgroundY = (pos.y * scaleFactorY - lensHeight / 2) * 2;

    lens.style.backgroundPosition = `-${backgroundX}px -${backgroundY}px`;
  }

  function getCursorPos(e) {
    const rect = video.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    return { x, y };
  }

  function captureVideoFrame(videoElement) {
    const canvas = document.createElement("canvas");
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/png");
  }
});
