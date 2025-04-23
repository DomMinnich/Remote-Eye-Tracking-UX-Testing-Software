// Dominic Minnich 2024
// js/aboutus3d.js

// Configuration options
const config = {
  draggable: true,
  enableWallpaperMovement: true,
  softOrbit: false, // true for soft orbit movement, false to disable
  softOrbitSpeed: 0.001, // Speed of the soft orbit movement
  orbitFocalDistance: 1,
};

// Set up the scene, camera, and renderer (existing code unchanged)
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.z = config.orbitFocalDistance;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.1);
scene.add(hemisphereLight);

const light = new THREE.PointLight(0xffffff, 2, 100);
light.position.set(0, 0, 0);
scene.add(light);

// Load the GLB model (existing code unchanged)
const loader = new THREE.GLTFLoader();
//model is stored in flaks static folder
loader.load(
  "/static/model.glb",
  function (gltf) {
    gltf.scene.traverse((child) => {
      if (child.isMesh) {
        child.material.transparent = true;
        child.material.opacity = 0;
        new TWEEN.Tween(child.material)
          .to({ opacity: 1 }, 2000)
          .easing(TWEEN.Easing.Quadratic.InOut)
          .start();
      }
    });
    scene.add(gltf.scene);
  },
  undefined,
  function (error) {
    console.error("An error occurred while loading the GLB model:", error);
  }
);

// Add OrbitControls for interaction
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.1;
controls.enableZoom = false;
controls.enablePan = false;
controls.rotateSpeed = 0.3;

if (!config.enableWallpaperMovement) {
  controls.enabled = false;
}

let softOrbitAngle = 3.14; // Initial angle for soft orbit movement

// Update UI elements with current config values
document.getElementById("draggable").checked = config.draggable;
document.getElementById("enableWallpaperMovement").checked =
  config.enableWallpaperMovement;
document.getElementById("softOrbit").checked = config.softOrbit;
document.getElementById("softOrbitSpeed").value = config.softOrbitSpeed;
document.getElementById("orbitFocalDistance").value = config.orbitFocalDistance;

// Add event listeners for UI controls
document.getElementById("draggable").addEventListener("change", (event) => {
  config.draggable = event.target.checked;
  controls.enabled = config.draggable && config.enableWallpaperMovement;
});

document
  .getElementById("enableWallpaperMovement")
  .addEventListener("change", (event) => {
    config.enableWallpaperMovement = event.target.checked;
    controls.enabled = config.draggable && config.enableWallpaperMovement;
  });

document.getElementById("softOrbit").addEventListener("change", (event) => {
  config.softOrbit = event.target.checked;
});

document.getElementById("softOrbitSpeed").addEventListener("input", (event) => {
  config.softOrbitSpeed = parseFloat(event.target.value);
});

document
  .getElementById("orbitFocalDistance")
  .addEventListener("input", (event) => {
    config.orbitFocalDistance = parseFloat(event.target.value);
    camera.position.z = config.orbitFocalDistance;
  });

function createInfoPanel(name, description, imageUrl, linkUrl) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  canvas.width = 512;
  canvas.height = 256;

  // Draw an opaque background with rounded corners to avoid blending issues
  context.fillStyle = "rgba(25, 25, 25, 0.04)"; // Fully opaque background
  context.beginPath();
  const radius = 20;
  context.moveTo(radius, 0);
  context.lineTo(canvas.width - radius, 0);
  context.quadraticCurveTo(canvas.width, 0, canvas.width, radius);
  context.lineTo(canvas.width, canvas.height - radius);
  context.quadraticCurveTo(
    canvas.width,
    canvas.height,
    canvas.width - radius,
    canvas.height
  );
  context.lineTo(radius, canvas.height);
  context.quadraticCurveTo(0, canvas.height, 0, canvas.height - radius);
  context.lineTo(0, radius);
  context.quadraticCurveTo(0, 0, radius, 0);
  context.closePath();
  context.fill();

  // Draw border with rounded corners
  context.strokeStyle = "white";
  context.lineWidth = 3;
  context.stroke();

  const image = new Image();
  image.src = imageUrl;
  image.onload = () => {
    // Draw the image without opacity adjustments
    context.globalAlpha = 1.0; // Ensure full opacity
    context.drawImage(image, 20, 20, 100, 100);

    // Draw text with clear, visible colors and outline
    context.globalAlpha = 1.0; // Ensure no transparency for text
    context.font = "bold " + "30px Quicksand";
    context.lineWidth = 3; // Thicker outline for better contrast
    context.strokeStyle = "black";
    context.fillStyle = "white";
    context.strokeText(name, 140, 50);
    context.fillText(name, 140, 50);

    context.font = "bold " + "23px Quicksand";
    context.lineWidth = 3; // Thicker outline for description
    context.strokeText(description, 140, 100);
    context.fillText(description, 140, 100);

    // Draw the link text with black outline
    context.font = "bold " + "20px Quicksand";
    context.lineWidth = 3; // Thicker outline for link text
    context.strokeStyle = "black";
    context.fillStyle = "#00bfff"; // Light blue
    context.strokeText("GitHub", 140, 150);
    context.fillText("GitHub", 140, 150);

    // Update the texture for the panel
    const texture = new THREE.CanvasTexture(canvas);
    panel.material.map = texture;
    panel.material.needsUpdate = true;
  };

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.MeshStandardMaterial({
    map: texture,
    transparent: true, // Disable transparency to avoid blending issues
    opacity: 1.0, // Ensure full opacity for clear display
    depthWrite: false,
    roughness: 0.1, // Reduce roughness to make the content clearer
    metalness: 0.3, // Adjust metalness to prevent dulling
    alphaTest: 0.01,
  });

  const geometry = new THREE.PlaneGeometry(2, 1);
  const panel = new THREE.Mesh(geometry, material);
  panel.renderOrder = 1;

  // Optional animations for the panel
  new TWEEN.Tween(panel.material)
    .to({ opacity: 1.0 }, 2000) // Keep opacity fully visible
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();

  panel.scale.set(1, 1, 1);
  new TWEEN.Tween(panel.scale)
    .to({ x: 2, y: 2, z: 2 }, 800)
    .easing(TWEEN.Easing.Elastic.Out)
    .start();

  // Add event listener for click event
  window.addEventListener("click", (event) => {
    const mouse = new THREE.Vector2();
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);

    const intersects = raycaster.intersectObject(panel);
    if (intersects.length > 0) {
      const intersect = intersects[0];
      const uv = intersect.uv;
      const x = uv.x * canvas.width;
      const y = (1 - uv.y) * canvas.height;

      // Check if the click is within the "Click here" text area
      if (x >= 140 && x <= 240 && y >= 130 && y <= 170) {
        window.open(linkUrl, "_blank");
      }
    }
  });

  return panel;
}

// Define team member data with links
const teamMembers = [
  {
    name: "Sulaiman Hussain",
    description: "Full Stack Developer",
    imageUrl: "static/images/pic.png",
    linkUrl: "https://example.com/sulaiman",
  },
  {
    name: "Dominic Minnich",
    description: "Team Leader\nFull Stack Developer",
    imageUrl: "static/images/pic.png",
    linkUrl: "https://github.com/DomMinnich",
  },
  {
    name: "Kyle Benich",
    description: "Full Stack Developer",
    imageUrl: "static/images/pic.png",
    linkUrl: "https://example.com/kyle",
  },
  {
    name: "Logan Smith",
    description: "Full Stack Developer",
    imageUrl: "static/images/pic.png",
    linkUrl: "https://github.com/lssmith80",
  },
];

// Create and position each infopanel with team member data
const panels = [];
const radius = 10;
teamMembers.forEach((member, index) => {
  const panel = createInfoPanel(
    member.name,
    member.description,
    member.imageUrl,
    member.linkUrl
  );
  panel.name = member.name; // Add name property for logging
  const angle = (index / teamMembers.length) * Math.PI * 2;
  panel.position.set(radius * Math.cos(angle), 0, radius * Math.sin(angle));
  panel.lookAt(0, 0, 0);

  panel.userData = { originalScale: panel.scale.clone() };
  panel.isVisible = false;

  scene.add(panel);
  panels.push(panel);
});

// Function to check if a panel is visible in the camera's view
function isPanelVisible(panel, camera) {
  const frustum = new THREE.Frustum();
  const cameraViewProjectionMatrix = new THREE.Matrix4();

  camera.updateMatrixWorld();
  camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
  cameraViewProjectionMatrix.multiplyMatrices(
    camera.projectionMatrix,
    camera.matrixWorldInverse
  );
  frustum.setFromProjectionMatrix(cameraViewProjectionMatrix);

  return frustum.intersectsObject(panel);
}

// Update the animation logic to scale the panel based on its visibility
function updatePanelVisibility() {
  panels.forEach((panel) => {
    const visible = isPanelVisible(panel, camera);
    if (visible && !panel.isVisible) {
      console.log(`Panel ${panel.name} is now visible`);
      panel.isVisible = true;
      new TWEEN.Tween(panel.scale)
        .to(
          {
            x: panel.userData.originalScale.x * 6,
            y: panel.userData.originalScale.y * 6,
            z: panel.userData.originalScale.z * 6,
          },
          200
        )
        .start();
    } else if (!visible && panel.isVisible) {
      console.log(`Panel ${panel.name} is now invisible`);
      panel.isVisible = false;
      new TWEEN.Tween(panel.scale)
        .to(
          {
            x: panel.userData.originalScale.x,
            y: panel.userData.originalScale.y,
            z: panel.userData.originalScale.z,
          },
          200
        )
        .start();
    }
  });
}

// Function to animate the camera to 180 degrees
function animateCameraTo180Degrees() {
  const targetPosition = { x: 0, y: 0, z: -config.orbitFocalDistance };
  const targetRotation = { x: 0, y: Math.PI, z: 0 };

  new TWEEN.Tween(camera.position)
    .to(targetPosition, 1000)
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();

  new TWEEN.Tween(camera.rotation)
    .to(targetRotation, 6000)
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();
}

// Initialize TWEEN for animations
function animate() {
  requestAnimationFrame(animate);
  if (config.enableWallpaperMovement) {
    if (config.draggable) {
      controls.update(); // Update the controls to enable dragging and interaction
    }

    if (config.softOrbit) {
      softOrbitAngle += config.softOrbitSpeed;
      camera.position.x = config.orbitFocalDistance * Math.sin(softOrbitAngle);
      camera.position.z = config.orbitFocalDistance * Math.cos(softOrbitAngle);
      camera.lookAt(scene.position);
    }
  }
  TWEEN.update();
  controls.update();
  updatePanelVisibility();
  renderer.render(scene, camera);
}
animate();

// Resizing handler
window.addEventListener("resize", () => {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
});

// Move camera to 180 degrees after reload
window.addEventListener("load", () => {
  animateCameraTo180Degrees();
});
