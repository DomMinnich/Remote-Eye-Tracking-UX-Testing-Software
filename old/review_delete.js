// review.js - Updated for Light Theme Redesign

// --- WebGazer Functionality ---
// Global variables (ensure they are defined, maybe move from inline script)
let webcamStream = null;
let gazeData = [];
let webgazerInitialized = false; // Track initialization

// Function to start WebGazer
function startWebGazer() {
    if (webgazerInitialized) {
        console.log("WebGazer already initialized.");
        webgazer.resume(); // Resume if paused
        webgazer.showVideo(true);
        webgazer.showPredictionPoints(true);
        updateWebGazerElements(); // Ensure elements are correctly styled/positioned
        return;
    }
    console.log("Initializing WebGazer...");

    webgazer
        .setRegression("ridge")
        .setGazeListener(function(data, clock) {
            if (data) {
                gazeData.push({ x: data.x, y: data.y, t: clock }); // Store with timestamp
                // Optional: Update gaze dot visually (if needed beyond CSS)
                // const gazeDot = document.getElementById('webgazerGazeDot');
                // if (gazeDot) { ... }
            }
        })
        .showVideo(true)
        .showPredictionPoints(true)
        .begin()
        .then(() => {
            console.log("WebGazer started successfully.");
            webgazerInitialized = true;
            updateWebGazerElements(); // Apply styles/positioning after init

            // Get webcam stream for display (if not already handled by WebGazer)
            if (!document.getElementById('webgazerVideoFeed')?.srcObject) {
                navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                    .then(stream => {
                        webcamStream = stream;
                        const videoFeed = document.getElementById('webgazerVideoFeed');
                        if (videoFeed) {
                            videoFeed.srcObject = stream;
                        }
                        console.log("Webcam stream acquired.");
                    }).catch(error => {
                        console.error("Error accessing webcam:", error);
                        alert("Could not access webcam. Eye tracking may not function correctly.");
                    });
            }
        }).catch(error => {
            console.error("Failed to start WebGazer:", error);
            alert("Failed to initialize eye tracking.");
        });
}

// Function to stop WebGazer
function stopWebGazer() {
    return new Promise((resolve) => {
        if (!webgazerInitialized || !webgazer) {
             console.log("WebGazer not initialized or running, nothing to stop.");
            resolve();
            return;
        }
        try {
            console.log("Stopping WebGazer...");
            webgazer.pause(); // Pause first
            webgazer.showVideo(false);
            webgazer.showPredictionPoints(false);
            // Optional: Decide whether to fully end or just pause
            // webgazer.end(); // Use end() if you want to clear state completely

            // Stop the manual webcam stream if it exists
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
                console.log("Manual webcam stream stopped.");
            }

             // Clear the video feed srcObject if WebGazer didn't
            const videoFeed = document.getElementById('webgazerVideoFeed');
            if (videoFeed && videoFeed.srcObject) {
                videoFeed.srcObject.getTracks().forEach(track => track.stop());
                videoFeed.srcObject = null;
            }

            console.log("WebGazer paused.");
            resolve();
        } catch (err) {
            console.error("Error stopping WebGazer:", err);
            resolve(); // Resolve anyway
        }
    });
}

// Function to update/ensure WebGazer element styling (Simplified)
function updateWebGazerElements() {
    // Check if container exists, CSS should handle positioning within it
    const container = document.querySelector('.webgazer-ui-container');
    if (!container) {
        console.warn("WebGazer UI container not found.");
        return;
    }

    // Ensure GazeDot exists (WebGazer might create it)
    let gazeDot = document.getElementById('webgazerGazeDot');
    if (!gazeDot && document.body) { // Check body exists before appending
        gazeDot = document.createElement('div');
        gazeDot.id = 'webgazerGazeDot';
        document.body.appendChild(gazeDot); // Append to body for fixed positioning
        console.log("Created #webgazerGazeDot");
    }
    // CSS should style the dot via its ID

    // Ensure video feed is inside the container (or handled by WebGazer placement)
    const videoFeed = document.getElementById('webgazerVideoFeed');
    // If WebGazer places it outside, we might need to move it, but let's rely on CSS first.

    // Face overlay and feedback box styling are mostly handled by WebGazer and targeted by CSS.
    // We might only need to ensure they are visible if WebGazer hides them unexpectedly.
    const faceOverlay = document.getElementById('webgazerFaceOverlay');
    const faceFeedbackBox = document.getElementById('webgazerFaceFeedbackBox');

    // Example: Ensure visibility if needed
    // if (faceOverlay) faceOverlay.style.display = 'block';
    // if (faceFeedbackBox) faceFeedbackBox.style.display = 'block';

    console.log("WebGazer elements checked/updated.");
}


// --- Session Recording & Task Management ---
// Global variables (ensure defined, maybe move from inline script)
let mediaRecorder = null;
let recordedChunks = [];
// let benchmarkMode = false; // Should be set from inline script
// let majorTasks = []; // Should be set from inline script
// let currentTaskIndex = 0;
// let taskStartTime = null;
// let taskTimes = [];
// let sessionStarted = false;
// let projectId = ""; // Should be set from inline script


// Function to display the current task
function displayTask(index) {
    const taskContainer = document.getElementById("task-container");
    const nextTaskBtn = document.getElementById("next-task");
    const majorTaskDisplay = document.getElementById("major-task");
    const minorTasksList = document.getElementById("minor-tasks");

    if (!taskContainer || !nextTaskBtn || !majorTaskDisplay || !minorTasksList) {
        console.error("Task display elements not found.");
        return;
    }

    if (index >= majorTasks.length) {
        taskContainer.style.display = "none";
        nextTaskBtn.style.display = "none";
        console.log("All tasks completed.");
        // Optional: Automatically end session after a delay
        // alert("Tasks complete! Session will end automatically.");
        // setTimeout(endSession, 2000);
        return;
    }

    const task = majorTasks[index];
    if (!task || !task.name) {
        console.error("Invalid task data at index:", index, task);
         majorTaskDisplay.innerText = "Error: Invalid Task";
         minorTasksList.innerHTML = "";
    } else {
        majorTaskDisplay.innerText = task.name;
        minorTasksList.innerHTML = ""; // Clear previous minor tasks

        if (task.minor_tasks && Array.isArray(task.minor_tasks)) {
            task.minor_tasks.forEach((minorTask) => {
                const li = document.createElement("li");
                li.className = 'review-page__task-display--minor-item'; // Add class for styling
                li.innerText = minorTask;
                minorTasksList.appendChild(li);
            });
        }
    }


    taskContainer.style.display = "block"; // Show the container
    nextTaskBtn.style.display = "inline-block"; // Show next button
}

// Function to start timing a task
function startTask(index) {
    if (index < majorTasks.length) {
        taskStartTime = performance.now(); // Use performance.now() for more accuracy
        console.log(`Starting task ${index + 1}: ${majorTasks[index]?.name}`);
        displayTask(index);
    } else {
        console.log("Attempted to start task beyond available tasks.");
        displayTask(index); // Still call displayTask to handle completion state
    }
}

// Function to end timing for the current task
function endTask() {
    if (sessionStarted && taskStartTime !== null && currentTaskIndex < majorTasks.length) {
        const endTime = performance.now();
        const timeSpent = (endTime - taskStartTime) / 1000; // Time in seconds
        const currentTaskName = majorTasks[currentTaskIndex]?.name;

        if (currentTaskName) {
            taskTimes.push({ task: currentTaskName, time: timeSpent });
            console.log(`Ended task ${currentTaskIndex + 1}: ${currentTaskName}, Time: ${timeSpent.toFixed(2)}s`);
        } else {
            console.warn("Could not record time for invalid task at index:", currentTaskIndex);
        }
        taskStartTime = null; // Reset for the next task
    }
}

// Function to start the recording session
async function startSession() {
    const startBtn = document.getElementById('start-session');
    const endBtn = document.getElementById('end-session');

    if (sessionStarted) {
        console.warn("Session already started.");
        return;
    }

    // Disable start button, show end button
    if (startBtn) startBtn.disabled = true;
    if (endBtn) endBtn.disabled = false;


    try {
        // Start screen recording
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { cursor: "always" },
            audio: false, // No audio recording for screen share usually
        });

        recordedChunks = []; // Reset chunks
        mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            console.log("MediaRecorder stopped.");
            // Stop the screen share tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.onerror = (event) => {
             console.error("MediaRecorder error:", event.error);
             alert(`Screen recording error: ${event.error.name}. Please try again.`);
             // Attempt cleanup even on error
             endSession(true); // Pass error flag maybe
        };

        mediaRecorder.start();
        console.log("Screen recording started.");

        // Start WebGazer
        startWebGazer();

        // Initialize first task
        sessionStarted = true;
        currentTaskIndex = 0;
        taskTimes = []; // Reset task times
        startTask(currentTaskIndex);

        // Hide the start button permanently after first successful start
        if (startBtn) startBtn.style.display = 'none';

    } catch (error) {
        console.error("Error starting session (getDisplayMedia or WebGazer):", error);
        alert(`Could not start session: ${error.name || error.message}. Please ensure you grant screen sharing permissions.`);
        // Reset button states if failed
        if (startBtn) startBtn.disabled = false;
        if (endBtn) endBtn.disabled = true;
        sessionStarted = false; // Ensure session isn't marked as started
    }
}

// Unified function to end the session and submit data
async function endSession(encounteredError = false) {
    const startBtn = document.getElementById('start-session');
    const endBtn = document.getElementById('end-session');
    const uploadIndicator = document.getElementById('upload-progress');

    if (!sessionStarted && !encounteredError) {
        console.warn("Session not started or already ended.");
        return;
    }

    console.log("Ending session...");
    sessionStarted = false; // Mark as ended immediately

    // Disable end button
    if (endBtn) endBtn.disabled = true;

    // Record time for the last active task
    endTask();

    // Show loading indicator
    if (uploadIndicator) uploadIndicator.style.display = 'block';

    // Stop screen recording (if active)
    let recordingPromise = Promise.resolve();
    if (mediaRecorder && mediaRecorder.state === "recording") {
        recordingPromise = new Promise(resolve => {
             mediaRecorder.onstop = () => {
                 console.log("MediaRecorder stopped during endSession.");
                 resolve(); // Resolve when stopped
             };
             mediaRecorder.onerror = (event) => {
                 console.error("MediaRecorder error on stop:", event.error);
                 resolve(); // Resolve even on error to proceed
             };
             mediaRecorder.stop();
        });
    }

    // Stop WebGazer
    let webgazerPromise = stopWebGazer();

    try {
        // Wait for recording and WebGazer to stop
        await Promise.all([recordingPromise, webgazerPromise]);
        console.log("Recording and WebGazer stopped/paused.");

        // Prepare FormData
        const formData = new FormData();
        formData.append("project_id", projectId);
        if (benchmarkMode) {
            formData.append("benchmark", "true");
        }
        formData.append("task_times", JSON.stringify(taskTimes));
        formData.append("gaze_data", JSON.stringify(gazeData)); // Send gaze data with upload

        // Append video blob
        if (recordedChunks.length > 0) {
            const blob = new Blob(recordedChunks, { type: "video/webm" });
             console.log("Video blob size:", Math.round(blob.size / 1024 / 1024 * 100) / 100, "MB");
            formData.append("video", blob, `review_${projectId}_${Date.now()}.webm`);
        } else {
            console.warn("No video chunks recorded.");
            // Optionally send an empty file or flag
            // const emptyBlob = new Blob([], { type: "video/webm" });
            // formData.append("video", emptyBlob, "empty_video.webm");
        }

         // Submit data
         console.log("Uploading data...");
        const response = await fetch("{{ url_for('main.upload') }}", { // Ensure URL is correct
            method: "POST",
            body: formData,
            // Add CSRF token if needed: headers: { 'X-CSRFToken': getCookie('csrf_token') }
        });

        console.log("Server response status:", response.status);
        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.error || `HTTP error! status: ${response.status}`);
        }

        console.log("Upload successful:", responseData);
        alert("Session uploaded successfully!");
        // Redirect to the broad review page
        window.location.href = `/viewReviewBroad/${projectId}`;

    } catch (error) {
        console.error("Error during session end or upload:", error);
        alert(`Failed to upload session: ${error.message}\n\nPlease check the console for details and try again.`);
        // Re-enable end button? Or guide user?
        // if (endBtn) endBtn.disabled = false; // Allow retry maybe?

    } finally {
        // Hide loading indicator
        if (uploadIndicator) uploadIndicator.style.display = 'none';
        // Reset state
        mediaRecorder = null;
        recordedChunks = [];
        taskTimes = [];
        gazeData = [];
        taskStartTime = null;
        currentTaskIndex = 0;
        // Reset button states for potential restart (if applicable)
        // if (startBtn) startBtn.style.display = 'inline-block'; // Show start again
        // if (startBtn) startBtn.disabled = false;
        // if (endBtn) endBtn.disabled = true; // Keep end disabled
    }
}


// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-session');
    const endBtn = document.getElementById('end-session');
    const nextTaskBtn = document.getElementById('next-task');

    if (startBtn) {
        startBtn.addEventListener('click', startSession);
    } else {
        console.error("#start-session button not found.");
    }

    if (endBtn) {
        endBtn.addEventListener('click', () => endSession());
        endBtn.disabled = true; // Initially disable end button
    } else {
        console.error("#end-session button not found.");
    }

    if (nextTaskBtn) {
        nextTaskBtn.addEventListener('click', function() {
            if (!sessionStarted) return;
            endTask(); // End timing for the current task
            currentTaskIndex++;
            startTask(currentTaskIndex); // Start timing for the next task
        });
    } else {
        console.error("#next-task button not found.");
    }

    // Initially hide task container if it exists
    const taskContainer = document.getElementById("task-container");
    if (taskContainer) {
        taskContainer.style.display = 'none';
    }
});