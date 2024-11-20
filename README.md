# Remote Eye-Tracking UX Testing Software

## Overview

This project is a Senior Capstone focused on developing an innovative software solution that enables remote eye-tracking during user experience (UX) testing. The software utilizes the built-in camera on users’ personal computers to capture and analyze eye movement data remotely, offering comprehensive insights into user interactions with digital products.

## Sponsor & Faculty Advisor

- **Sponsor**: PFW CS Department
- **Faculty Advisor**: Prof. Jay Johns

## Team Members

- Dominic Minnich (Team Leader)
- Kyle Benich
- Logan Smith
- Sulaiman Hussain

## Project Type

- ☒ Application Development
- ☐ Research-focused
- ☐ Information Systems

## Project Description

The goal of this project is to develop a software tool that allows for remote UX testing by tracking eye movements using the built-in cameras of users' devices. By leveraging advanced algorithms, the software processes video feeds to provide quantitative data on user focus areas during digital interactions.

## Vision Explanation -Dominic Minnich (Team Leader)
For much better zoom quality go here🔎:
[Vision_Explanation_Nov20.pdf](https://github.com/user-attachments/files/17833629/Vision_Explanation_Nov20.pdf)
![Vision_Explanation _Nov20](https://github.com/user-attachments/assets/fe02e7a7-1d78-4e58-b5a7-604948fa8290)


### Key Features

1. **Camera-Based Eye Tracking**: Tracks eye movement using standard webcams, eliminating the need for specialized hardware.
2. **Remote Testing Capability**: UX testers can participate from any location, increasing flexibility and diversity in testing environments.
3. **Data Collection and Analysis**: Collects detailed data on user focus points, gaze paths, and interaction times, facilitating in-depth analysis.
4. **User Privacy and Security**: Implements secure encryption, consent protocols, and data anonymization to protect user privacy.
5. **Real-Time and Post-Session Reporting**: Offers real-time feedback during sessions and detailed reports afterward for comprehensive insights.

## Goals

- **Enhance Remote UX Testing**: Provide a tool that removes geographical constraints, making UX testing more accessible.
- **Improve Data Accuracy**: Capture real-time eye movement data to gain precise insights into user behavior and preferences.
- **Increase Accessibility**: Use widely available hardware to make high-quality UX testing available to a broader audience.

## Target Audience

- UX Researchers and Designers
- Product Managers
- Companies conducting large-scale remote UX testing
- PFW students in Software Development or UX courses

## Expected Impact

This software aims to revolutionize UX testing by eliminating physical barriers and providing detailed, actionable data. The resulting insights will enable teams to make informed design decisions, leading to improved user experiences across digital platforms.

## Team Size

- ☒ 4 Members
- ☒ >4 Members

## Required Backgrounds

- Frontend Development
- Backend Development
- Data Analysis

## Development Stack

### Frontend Development

- **JavaScript**: For building interactive, real-time interfaces.
- **HTML/CSS**: For site structure and styling.
- **WebRTC**: For handling real-time communication and video streams.

### Backend Development

- **Python**: Ideal for computer vision and data analysis.
- **Flask**: Framework for building scalable web applications.
- **OpenCV**: For image processing and eye-tracking algorithms.
- **TensorFlow or PyTorch**: For advanced computer vision tasks.

### Computer Vision and Eye-Tracking

- **WebGazer.js: Eye tracking script.

### Data Storage

- **SQlite**

### Data Analysis and Reporting

- **Pandas/Numpy**: For data manipulation and analysis.
- **Matplotlib/Seaborn**: For creating detailed visual reports.
- **Jupyter Notebooks**: For shareable analysis reports and exploratory data analysis.

### Deployment

- **Docker**: For containerizing the application.

### Requirements

## Functional Requirements

Users can create, edit, and delete their profiles, except for guests whose data won’t be saved.
Users can create new projects with tasks, descriptions, and URLs.
The system tracks eye movements in real-time using standard webcams.
The system records sessions, combining screen recordings with eye-tracking overlays.
Users can select roles (e.g., Analyst, Project Manager, Admin) and perform tasks based on those roles.

## Non-Functional Requirements
-**Performance**: Must handle real-time data processing with minimal latency.
-**Usability**: The system should comply with WCAG 2.1 Level AA accessibility guidelines.
-**Security**: Use AES-256 encryption and multi-factor authentication.
-**Scalability**: Support large datasets and concurrent users.

### Security and Compliance

- **SSL/TLS**: For securing data in transit.
- **OAuth2**: For secure user authentication and authorization.

### Additional Tools

- **WebAssembly (Wasm)**: For high-performance computing in the browser.

## Why This Stack?

- **Scalability**: Designed to handle large amounts of data and users.
- **Performance**: Supports real-time video processing and eye-tracking.
- **Flexibility**: Combines powerful backend data processing with a user-friendly frontend.
- **Community Support**: Strong community support for chosen technologies.

## Stretch Goals
-**Mobile Support**: Add support for mobile phones to capture eye-tracking data.
-**Heat Mapping**: Extract heat maps from user behavior data, highlighting areas of focus on the screen.
-**Domain Expansion**: Extend support beyond specific domains like Figma to other established or custom websites.

## Methodology
-**Agile Development**: The team will adopt an Agile methodology to enable continuous improvement based on testing and feedback.

## Technology Disclosure

- No NDA or IP Assignment Agreement requested.

## Conclusion

This project will deliver a robust and scalable eye-tracking software solution that supports remote UX testing. By using widely available technology, it will provide valuable insights to enhance digital product design, making UX testing more accessible and effective.
