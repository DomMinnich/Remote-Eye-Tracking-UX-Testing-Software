// script.js

// Select the iris and pupil elements
const iris = document.querySelector('.iris');

// Function to move the iris towards the cursor
function moveEye(event) {
    const eyeRect = iris.parentNode.getBoundingClientRect();
    const eyeCenterX = eyeRect.left + eyeRect.width / 2;
    const eyeCenterY = eyeRect.top + eyeRect.height / 2;

    const angle = Math.atan2(event.clientY - eyeCenterY, event.clientX - eyeCenterX);

    // Constrain the iris movement within the sclera boundary
    const irisMoveDistance = 15;
    const irisX = irisMoveDistance * Math.cos(angle);
    const irisY = irisMoveDistance * Math.sin(angle);

    iris.style.transform = `translate(${irisX}px, ${irisY}px)`;
}

// Add mousemove event listener to the document
document.addEventListener('mousemove', moveEye);
