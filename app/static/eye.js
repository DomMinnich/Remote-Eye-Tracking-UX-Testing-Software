// Dominic Minnich 2024
// script.js  


// This script is used to move the iris and eyelid elements in response to mouse movement.
// It also triggers a blink animation when the user clicks on the eye.
// It also applies a warning class to the eye container if there is an error alert.


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

// Function to trigger grow animation on the pupil
function blinkEye() {
    pupil.classList.add('grow');

    // Remove the class after the animation ends
    setTimeout(() => {
        pupil.classList.remove('grow');
    }, 1500); // Match the animation duration
}

// Add mousemove event listener to track cursor
document.addEventListener('mousemove', moveEye);

// Add click event listener to trigger the blink
document.addEventListener('click', blinkEye);


// Apply warning class if there is an error alert
document.addEventListener('DOMContentLoaded', () => {
    const flashMessage = document.querySelector('.alert-danger');
    const eyeContainer = document.querySelector('.eye-container');
    const pupil = document.querySelector('.pupil');

    if (flashMessage) {
        // Add the warning class to trigger color change and pupil growth
        eyeContainer.classList.add('warning'); 
        
        // Remove the warning class after 5 seconds
        setTimeout(() => {
            eyeContainer.classList.remove('warning'); // Remove warning class
        }, 5000);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const loginPage = document.querySelector('.login-page');
    const successMessage = document.querySelector('.alert-success');  // Detect success message
    const eyeContainer = document.querySelector('.eye-container');
    
    if (successMessage) {
        eyeContainer.classList.add('success');  // Trigger success animation (green)
        loginPage.classList.add('zoom-effect');  // Trigger zoom effect
        // Delay redirection to allow animation to complete
        setTimeout(() => {
            window.location.href = "/";  // Redirect to home
        }, 800);  // Match CSS animation duration
    }
});





