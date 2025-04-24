// js/aboutus3d.js - Updated for Light Theme Redesign

// Configuration options (Keep or adjust as needed)
const config = {
  draggable: true,
  enableWallpaperMovement: true,
  softOrbit: false,
  softOrbitSpeed: 0.001,
  orbitFocalDistance: 10, // Adjusted initial distance for potentially smaller panels
};

// --- Scene Setup (Largely unchanged) ---
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.z = config.orbitFocalDistance;

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); // Use alpha for transparency if needed
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000000, 0); // Set clear color to transparent if body background is desired
document.body.appendChild(renderer.domElement); // Appends directly to body

// Basic Lighting
scene.add(new THREE.AmbientLight(0xffffff, 0.6)); // Softer ambient light
const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);

// --- Model Loading (Unchanged logic, ensure path is correct) ---
const loader = new THREE.GLTFLoader();
loader.load(
  "/static/model.glb", // Ensure this path is correct
  function (gltf) {
    const model = gltf.scene;
    // Center and scale model if necessary
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center); // Center the model
    // Optional scaling: model.scale.set(0.5, 0.5, 0.5);

    // Fade in material
    model.traverse((child) => {
      if (child.isMesh) {
        child.material.transparent = true;
        child.material.opacity = 0;
        new TWEEN.Tween(child.material)
          .to({ opacity: 1 }, 2000)
          .easing(TWEEN.Easing.Quadratic.InOut)
          .start();
      }
    });
    scene.add(model);
  },
  undefined,
  function (error) {
    console.error("Error loading GLB model:", error);
  }
);

// --- Orbit Controls (Unchanged logic) ---
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.1;
controls.enableZoom = false; // Zoom disabled as before
controls.enablePan = false; // Pan disabled as before
controls.rotateSpeed = 0.4; // Slightly faster?
controls.target.set(0, 0, 0); // Ensure controls target the center

// Apply initial wallpaper movement setting
if (!config.enableWallpaperMovement) {
  controls.enabled = false;
}

// --- UI Controls Event Listeners (Selectors should match new HTML) ---
const draggableCheckbox = document.getElementById("draggable");
const wallpaperCheckbox = document.getElementById("enableWallpaperMovement");
const softOrbitCheckbox = document.getElementById("softOrbit");
const speedSlider = document.getElementById("softOrbitSpeed");
const distanceInput = document.getElementById("orbitFocalDistance");

if (draggableCheckbox) draggableCheckbox.checked = config.draggable;
if (wallpaperCheckbox)
  wallpaperCheckbox.checked = config.enableWallpaperMovement;
if (softOrbitCheckbox) softOrbitCheckbox.checked = config.softOrbit;
if (speedSlider) speedSlider.value = config.softOrbitSpeed;
if (distanceInput) distanceInput.value = config.orbitFocalDistance;

draggableCheckbox?.addEventListener("change", (event) => {
  config.draggable = event.target.checked;
  controls.enabled = config.draggable && config.enableWallpaperMovement;
});

wallpaperCheckbox?.addEventListener("change", (event) => {
  config.enableWallpaperMovement = event.target.checked;
  controls.enabled = config.draggable && config.enableWallpaperMovement;
});

softOrbitCheckbox?.addEventListener("change", (event) => {
  config.softOrbit = event.target.checked;
});

speedSlider?.addEventListener("input", (event) => {
  config.softOrbitSpeed = parseFloat(event.target.value);
});

distanceInput?.addEventListener("input", (event) => {
  config.orbitFocalDistance = parseFloat(event.target.value);
  // Adjust camera position based on distance (maintaining soft orbit if active)
  const currentAngle = softOrbitAngle; // Use the current angle
  camera.position.x = config.orbitFocalDistance * Math.sin(currentAngle);
  // camera.position.y = 0; // Assuming orbit is horizontal
  camera.position.z = config.orbitFocalDistance * Math.cos(currentAngle);
  camera.lookAt(scene.position); // Ensure camera still looks at the center
});

// --- Info Panel Creation (REDESIGNED FOR LIGHT THEME) ---
function createInfoPanel(name, description, imageUrl, linkUrl) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  const scale = 2; // Increase resolution for sharper text/images
  canvas.width = 512 * scale;
  canvas.height = 256 * scale;

  // --- Style Variables (match CSS variables conceptually) ---
  const panelBgColor = "rgba(255, 255, 255, 0.95)"; // Light background
  const borderColor = "#A8D8EA"; // Soft Teal/Blue border
  const textColor = "#343A40"; // Dark Grey text
  const linkColor = "#7AC1D6"; // Darker Teal for link
  const nameFont = `bold ${30 * scale}px Poppins`;
  const descFont = `normal ${22 * scale}px Inter`;
  const linkFont = `500 ${20 * scale}px Inter`; // Medium weight for link
  const borderRadius = 20 * scale;
  const padding = 25 * scale;
  const imageSize = 100 * scale;
  const textStartX = padding + imageSize + 20 * scale; // X position for text start

  // --- Drawing ---
  context.fillStyle = panelBgColor;
  context.strokeStyle = borderColor;
  context.lineWidth = 4 * scale; // Slightly thicker border

  // Draw rounded rectangle background
  context.beginPath();
  context.moveTo(borderRadius, 0);
  context.lineTo(canvas.width - borderRadius, 0);
  context.quadraticCurveTo(canvas.width, 0, canvas.width, borderRadius);
  context.lineTo(canvas.width, canvas.height - borderRadius);
  context.quadraticCurveTo(
    canvas.width,
    canvas.height,
    canvas.width - borderRadius,
    canvas.height
  );
  context.lineTo(borderRadius, canvas.height);
  context.quadraticCurveTo(0, canvas.height, 0, canvas.height - borderRadius);
  context.lineTo(0, borderRadius);
  context.quadraticCurveTo(0, 0, borderRadius, 0);
  context.closePath();
  context.fill();
  context.stroke(); // Draw border after filling

  // Load and draw image
  const image = new Image();
  image.crossOrigin = "Anonymous"; // If loading from different origin
  image.src = imageUrl;
  image.onload = () => {
    // Draw image (rounded corners optional)
    context.save();
    context.beginPath();
    context.arc(
      padding + imageSize / 2,
      padding + imageSize / 2,
      imageSize / 2,
      0,
      Math.PI * 2,
      true
    );
    context.closePath();
    context.clip(); // Clip to circle
    context.drawImage(image, padding, padding, imageSize, imageSize);
    context.restore(); // Restore context state

    // Draw Text
    context.fillStyle = textColor;
    context.font = nameFont;
    context.fillText(name, textStartX, padding + 35 * scale); // Adjust Y position

    context.font = descFont;
    // Handle multi-line description
    const lines = description.split("\n");
    let currentY = padding + 80 * scale; // Starting Y for description
    lines.forEach((line) => {
      context.fillText(line, textStartX, currentY);
      currentY += 28 * scale; // Line height for description
    });

    // Draw Link Text
    context.fillStyle = linkColor;
    context.font = linkFont;
    context.fillText(
      "View GitHub",
      textStartX,
      canvas.height - padding - 10 * scale
    ); // Position link at bottom

    // IMPORTANT: Update texture after drawing is complete
    texture.needsUpdate = true;
  };
  image.onerror = () => {
    console.error("Failed to load image:", imageUrl);
    // Draw placeholder text if image fails
    context.fillStyle = "#CCCCCC";
    context.font = `italic ${18 * scale}px Inter`;
    context.textAlign = "center";
    context.fillText(
      "[Image]",
      padding + imageSize / 2,
      padding + imageSize / 2 + 6 * scale
    );
    context.textAlign = "left"; // Reset alignment
    texture.needsUpdate = true;
  };

  // --- Material and Mesh ---
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true; // Initial update

  const material = new THREE.MeshStandardMaterial({
    map: texture,
    transparent: true, // Allow transparency from RGBA background
    opacity: 1.0,
    side: THREE.DoubleSide, // Render both sides
    depthWrite: true, // Needed for correct layering if panels overlap
    roughness: 0.7, // Less glossy
    metalness: 0.1,
  });

  const geometry = new THREE.PlaneGeometry(2 * scale, 1 * scale); // Adjust geometry size if needed
  const panel = new THREE.Mesh(geometry, material);
  panel.scale.set(1 / scale, 1 / scale, 1 / scale); // Scale mesh down to compensate for larger canvas

  // Add userData for link and click handling
  panel.userData = { linkUrl: linkUrl, name: name };

  // --- Animation (Fade-in, scale optional) ---
  panel.material.opacity = 0; // Start invisible
  new TWEEN.Tween(panel.material)
    .to({ opacity: 1 }, 1500)
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();

  // Optional: Scale animation
  /*
      panel.scale.set(0.1/scale, 0.1/scale, 1/scale);
      new TWEEN.Tween(panel.scale)
          .to({ x: 1/scale, y: 1/scale, z: 1/scale }, 800)
          .easing(TWEEN.Easing.Elastic.Out)
          .delay(500) // Delay scale animation
          .start();
      */

  return panel;
}

// --- Team Member Data (Keep unchanged) ---
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

// --- Create and Position Panels ---
const panels = [];
const radius = 5; // Radius for panel circle
teamMembers.forEach((member, index) => {
  const panel = createInfoPanel(
    member.name,
    member.description,
    member.imageUrl,
    member.linkUrl
  );
  const angle = (index / teamMembers.length) * Math.PI * 2;
  panel.position.set(radius * Math.cos(angle), 0, radius * Math.sin(angle));
  panel.lookAt(0, 0, 0); // Make panels face the center
  scene.add(panel);
  panels.push(panel);
});

// --- Click Handling ---
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onPanelClick(event) {
  // Calculate mouse position in normalized device coordinates (-1 to +1)
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  // Update the picking ray with the camera and mouse position
  raycaster.setFromCamera(mouse, camera);

  // Calculate objects intersecting the picking ray
  const intersects = raycaster.intersectObjects(panels);

  if (intersects.length > 0) {
    // Intersected with the closest panel
    const clickedPanel = intersects[0].object;
    if (clickedPanel.userData.linkUrl) {
      window.open(clickedPanel.userData.linkUrl, "_blank");
    }
  }
}
window.addEventListener("click", onPanelClick);

// --- Animation Loop ---
let softOrbitAngle = Math.PI; // Initial angle slightly offset

function animate() {
  requestAnimationFrame(animate);
  TWEEN.update(); // Update animations

  if (config.enableWallpaperMovement) {
    if (config.draggable) {
      controls.update(); // Update OrbitControls if dragging enabled
    }

    // Soft orbit independent of dragging (if enabled)
    if (config.softOrbit) {
      softOrbitAngle += config.softOrbitSpeed;
      camera.position.x = config.orbitFocalDistance * Math.sin(softOrbitAngle);
      camera.position.z = config.orbitFocalDistance * Math.cos(softOrbitAngle);
      camera.lookAt(scene.position); // Keep looking at the center
      if (!config.draggable) controls.update(); // Need to update controls even if not dragging for lookAt to apply smoothly
    }
  } else {
    // Ensure controls don't update if wallpaper movement is off
    // (Handled by setting controls.enabled based on config)
  }

  renderer.render(scene, camera);
}
animate();

// --- Resizing Handler ---
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// --- Initial Animation (Camera move - Optional) ---
function animateCameraToStartPosition() {
  // Example: Move camera slightly back and rotate
  new TWEEN.Tween(camera.position)
    .to({ x: 0, y: 1, z: config.orbitFocalDistance + 2 }, 2000) // Move back slightly
    .easing(TWEEN.Easing.Quadratic.InOut)
    .start();

  // Rotate camera slightly if desired
  // new TWEEN.Tween(camera.rotation)...
}

// Call initial animation after a delay maybe
// setTimeout(animateCameraToStartPosition, 500);
