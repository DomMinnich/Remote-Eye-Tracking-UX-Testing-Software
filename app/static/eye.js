// script.js

// Select the iris and eyelid elements
const iris = document.querySelector('.cyber-iris');
const upperEyelid = document.querySelector('.upper-eyelid');
const lowerEyelid = document.querySelector('.lower-eyelid');
const pupil = document.querySelector('.pupil');

// Function to move the iris towards the cursor
function moveEye(event) {
    const eyeRect = iris.parentNode.getBoundingClientRect();
    const eyeCenterX = eyeRect.left + eyeRect.width / 2;
    const eyeCenterY = eyeRect.top + eyeRect.height / 2;

    const angle = Math.atan2(event.clientY - eyeCenterY, event.clientX - eyeCenterX);

    // Constrain the iris movement within a limited range
    const irisMoveDistance = 15;
    const irisX = irisMoveDistance * Math.cos(angle);
    const irisY = irisMoveDistance * Math.sin(angle);

    iris.style.transform = `translate(${irisX}px, ${irisY}px)`;
}

// Function to trigger the blink animation
function blinkEye() {
    // Add the "blinking" class to trigger animation
    //upperEyelid.classList.add('blink');
    //lowerEyelid.classList.add('blink');
    pupil.classList.add('grow');

    // Remove the class after the animation ends
    setTimeout(() => {
        //upperEyelid.classList.remove('blink');
        //lowerEyelid.classList.remove('blink');
        pupil.classList.remove('grow');
    }, 1500); // Match the animation duration
}

// Add mousemove event listener to track cursor
document.addEventListener('mousemove', moveEye);

// Add click event listener to trigger the blink
document.addEventListener('click', blinkEye);
