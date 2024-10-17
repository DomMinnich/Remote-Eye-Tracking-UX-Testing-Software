//Script for the app

/*
      CONTENTS OF THIS FILE
 NavMenu A->Z             | ~Line 10-56   -Dominic Minnich
 .?.?.                    | ~Line ?-?   

 */

// NavMenu A->Z

// Select elements
const menuToggle = document.querySelector(".menu-toggle");
const sidebarMenu = document.querySelector(".sidebar-menu");
const closeBtn = document.querySelector(".close-btn");
const expandableItems = document.querySelectorAll(".menu-list > li");

// Set initial max-height for submenus
expandableItems.forEach((item) => {
  const submenu = item.querySelector(".submenu");
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
    const submenu = item.querySelector(".submenu");
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


// .?.?.
