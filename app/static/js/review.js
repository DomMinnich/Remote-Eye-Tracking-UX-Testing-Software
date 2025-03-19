// WebGazer functionality
let webcamStream;

// Function to start WebGazer
function startWebGazer() {
  webgazer
    .setRegression("ridge")
    .setGazeListener(function (data, clock) {
      if (data) {
        console.log(data);
      }
    })
    .showVideo(true)
    .showPredictionPoints(true)
    .begin();

  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then(function (stream) {
      webcamStream = stream;

      const video = document.getElementById("webgazerVideoFeed");
      if (video) {
        video.srcObject = webcamStream;
        video.classList.add("review-video-feed");
      }
    })
    .catch(function (error) {
      console.error("Error accessing the webcam: ", error);
    });

  updateWebGazerElements();
}

function stopWebGazer() {
  return new Promise((resolve, reject) => {
    // Save the webgazer model data before ending the session
    webgazer.saveData()
      .then(function() {
        console.log("WebGazer data saved successfully");
        
        // Now end the webgazer session
        webgazer.end();
        console.log("Stopping WebGazer...");

        if (webcamStream) {
          const tracks = webcamStream.getTracks();
          tracks.forEach((track) => track.stop());
          webcamStream = null;
        }

        webgazer.showVideo(false);
        webgazer.showPredictionPoints(false);
        
        resolve(); // Successfully stopped webgazer
      })
      .catch(function(err) {
        console.error("Error saving WebGazer data:", err);
        // Continue with stopping even if save fails
        webgazer.end();
        
        if (webcamStream) {
          const tracks = webcamStream.getTracks();
          tracks.forEach((track) => track.stop());
          webcamStream = null;
        }
        
        webgazer.showVideo(false);
        webgazer.showPredictionPoints(false);
        
        resolve(); // Resolve even if there was an error
      });
  });
}

function updateWebGazerElements() {
  const gazeDot = document.getElementById("webgazerGazeDot");
  if (gazeDot) {
    gazeDot.style.opacity = "1";
    gazeDot.style.backgroundColor = "blue";
  }

  const videoElement = document.getElementById("webgazerVideoFeed");
  if (videoElement) {
    videoElement.classList.add("review-video-feed");
  }

  const faceOverlay = document.getElementById("webgazerFaceOverlay");
  if (faceOverlay) {
    faceOverlay.classList.add("review-face-overlay");
  }

  const faceFeedbackBox = document.getElementById("webgazerFaceFeedbackBox");
  if (faceFeedbackBox && videoElement) {
    const videoRect = videoElement.getBoundingClientRect();
    const feedbackWidth = faceFeedbackBox.offsetWidth;
    const feedbackHeight = faceFeedbackBox.offsetHeight;

    faceFeedbackBox.style.position = "fixed";
    faceFeedbackBox.style.left = `${
      videoRect.left + (videoRect.width - feedbackWidth) / 2
    }px`;
    faceFeedbackBox.style.top = `${
      videoRect.top + (videoRect.height - feedbackHeight) / 2
    }px`;
    faceFeedbackBox.style.pointerEvents = "none";
    faceFeedbackBox.style.zIndex = "1001";
  }
}

// Session and recording functionality
let mediaRecorder;
let recordedChunks = [];
let benchmarkMode = false;

// Unified function to end the session and submit data
function endSession() {
  console.log("End session function called");
  
  // First record the time for the last task
  if (sessionStarted && taskStartTime !== null) {
    endTask(); // Record time for the last task
    sessionStarted = false;
  }
  
  // Display a loading indicator
  const loadingMessage = document.createElement('div');
  loadingMessage.id = 'upload-progress';
  loadingMessage.style.position = 'fixed';
  loadingMessage.style.top = '50%';
  loadingMessage.style.left = '50%';
  loadingMessage.style.transform = 'translate(-50%, -50%)';
  loadingMessage.style.backgroundColor = 'rgba(0,0,0,0.8)';
  loadingMessage.style.color = 'white';
  loadingMessage.style.padding = '20px';
  loadingMessage.style.borderRadius = '10px';
  loadingMessage.style.zIndex = '9999';
  loadingMessage.innerHTML = 'Uploading session data...<br>Please do not close this page.';
  document.body.appendChild(loadingMessage);
  
  // Create a variable to store our form data
  let formData = new FormData();
  formData.append("project_id", projectId);
  
  console.log("Project ID being sent:", projectId);
  
  // If benchmark mode is active, include that flag
  if (benchmarkMode) {
    formData.append("benchmark", "true");
    console.log("Benchmark mode enabled");
  }
  
  // Append task times to the form data
  formData.append("task_times", JSON.stringify(taskTimes));
  console.log("Task times data:", JSON.stringify(taskTimes));
  
  let submissionPromise;
  
  // If we have recorded video, process it
  if (mediaRecorder && recordedChunks.length > 0) {
    console.log("Video chunks collected:", recordedChunks.length);
    const blob = new Blob(recordedChunks, { type: "video/webm" });
    console.log("Video blob size:", Math.round(blob.size / 1024 / 1024 * 100) / 100, "MB");
    formData.append("video", blob, "recorded_video.webm");
  } else {
    console.warn("No video data recorded - creating empty placeholder");
    // Create an empty video blob as a placeholder
    const emptyBlob = new Blob([], { type: "video/webm" });
    formData.append("video", emptyBlob, "empty_video.webm");
  }
  
  // Stop media recorder if it's running
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    try {
      mediaRecorder.stop();
      // Wait a bit for the mediaRecorder.onstop to fire and add data
      submissionPromise = new Promise(resolve => {
        setTimeout(() => {
          // Update formData with any new chunks
          if (recordedChunks.length > 0) {
            const blob = new Blob(recordedChunks, { type: "video/webm" });
            formData.delete("video"); // Remove the old video if it exists
            formData.append("video", blob, "recorded_video.webm");
            console.log("Updated video blob size after recorder stopped:", 
                      Math.round(blob.size / 1024 / 1024 * 100) / 100, "MB");
          }
          resolve();
        }, 2000); // Increase timeout to ensure data is processed
      });
    } catch (e) {
      console.error("Error stopping media recorder:", e);
      submissionPromise = Promise.resolve();
    }
  } else {
    // If mediaRecorder isn't active, just resolve immediately
    submissionPromise = Promise.resolve();
  }
  
  // Chain all the promises
  stopWebGazer()
    .then(() => {
      console.log("WebGazer stopped successfully");
      return submissionPromise;
    })
    .then(() => {
      console.log("Preparing to upload data...");
      // Add a CSRF token if your server requires it
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      if (csrfToken) {
        formData.append('csrf_token', csrfToken);
      }
      
      // Now submit the form data with a longer timeout
      return fetch("/upload", {
        method: "POST",
        body: formData,
        timeout: 120000 // 2 minute timeout
      });
    })
    .then((response) => {
      console.log("Server response status:", response.status);
      if (!response.ok) {
        return response.text().then(text => {
          throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      console.log("Upload successful", data);
      // Remove loading message
      document.body.removeChild(document.getElementById('upload-progress'));
      // Redirect to the review page or show a success message
      alert("Session uploaded successfully!");
      window.location.href = `/viewReviewBroad/${projectId}`;
    })
    .catch((error) => {
      console.error("Error during upload:", error);
      // Remove loading message
      document.body.removeChild(document.getElementById('upload-progress'));
      
      // Show more detailed error message
      const errorDetail = error.message || "Unknown error";
      alert(`Failed to upload session: ${errorDetail}\n\nPlease try again or contact support if the issue persists.`);
    });
}

// Start recording session
async function startSession() {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        cursor: "always",
      },
      audio: false,
    });

    mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.start();
    startWebGazer();
    
    // Start the first task
    sessionStarted = true;
    startTask(currentTaskIndex);
    
    // Hide the start button after pressing it
    document.getElementById("start-session").style.display = "none";
  } catch (error) {
    console.error("Error accessing display media.", error);
  }
}

// Task management functionality
let majorTasks = [];
let currentTaskIndex = 0;
let taskStartTime = null;
let taskTimes = [];
let sessionStarted = false;
let projectId = "";

function displayTask(index) {
  if (index >= majorTasks.length) {
    // Hide task display if we've gone through all tasks
    document.getElementById("task-container").style.display = "none";
    document.getElementById("next-task").style.display = "none";
    
    // Reset currentTaskIndex to prevent out of bounds errors
    currentTaskIndex = Math.max(0, majorTasks.length - 1);
    
    // Show tasks complete alert
    alert("Tasks complete! Session will end automatically.");
    
    // After a short delay, end the session automatically
    setTimeout(() => {
      endSession();
    }, 3000); // 3 second delay before ending session
    
    return;
  }

  const majorTask = majorTasks[index];
  document.getElementById("major-task").innerText = majorTask.name;
  const minorTasksContainer = document.getElementById("minor-tasks");
  minorTasksContainer.innerHTML = "";
  
  majorTask.minor_tasks.forEach((minorTask) => {
    const li = document.createElement("li");
    li.innerText = minorTask;
    minorTasksContainer.appendChild(li);
  });

  // Show the tasks container if it was hidden
  document.getElementById("task-container").style.display = "block";
  document.getElementById("next-task").style.display = "block";
}

function startTask(index) {
  taskStartTime = new Date();
  displayTask(index);
}

function endTask() {
  if (taskStartTime !== null) {
    const endTime = new Date();
    const timeSpent = (endTime - taskStartTime) / 1000; // time in seconds
    
    // Check if currentTaskIndex is valid before accessing majorTasks array
    if (currentTaskIndex >= 0 && currentTaskIndex < majorTasks.length) {
      taskTimes.push({ task: majorTasks[currentTaskIndex].name, time: timeSpent });
    } else {
      console.log("Task index out of bounds, recording time for unknown task");
      taskTimes.push({ task: "Unknown task", time: timeSpent });
    }
  }
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize observer for WebGazer elements
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.target.id === "webgazerFaceFeedbackBox") {
        updateWebGazerElements();
      }
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
  });

  // Set up event listeners
  document.getElementById("start-session").addEventListener("click", startSession);
  document.getElementById("end-session").addEventListener("click", endSession);
  
  document.getElementById("next-task").addEventListener("click", function() {
    if (!sessionStarted) return;
    endTask();
    currentTaskIndex++;
    
    // If we've reached the end of tasks, end the session
    if (currentTaskIndex >= majorTasks.length) {
      alert("You've completed all tasks! The session will now end.");
      
      // End the session after a brief delay to give the user time to see the alert
      setTimeout(() => {
        endSession();
      }, 1500);
      return;
    }
    
    // Otherwise, start the next task
    startTask(currentTaskIndex);
  });

  // Initially hide the tasks container
  const tasksContainer = document.getElementById("task-container");
  if (tasksContainer) {
    tasksContainer.style.display = "none";
  }
  document.getElementById("next-task").style.display = "none";
});
