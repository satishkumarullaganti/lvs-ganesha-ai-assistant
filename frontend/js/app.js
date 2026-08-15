const sendButton = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const chatContainer = document.getElementById("chat-container");
const chatWithAiBtn = document.getElementById("chat-with-ai-btn");

// ======================================
// Chat with AI Button
// ======================================
// Scrolls to the chat area and focuses the
// input so the user can start typing right away.

chatWithAiBtn.addEventListener("click", function () {

    chatContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    userInput.focus();

});
// ======================================
// Quick Registration Modal
// ======================================

const quickRegisterCard = document.getElementById("quick-register-card");

const registrationModal = document.getElementById("registration-modal");

const closeModal = document.getElementById("close-modal");

const registrationChoiceModal =
    document.getElementById("registration-choice-modal");

const closeRegistrationChoice =
    document.getElementById("close-registration-choice");

const registerByForm =
    document.getElementById("register-by-form");

const registerByChat =
    document.getElementById("register-by-chat");

const cancelRegistrationChoice =
    document.getElementById("cancel-registration-choice");

const registerSubmitBtn = document.getElementById("register-submit");

const competitionField = document.getElementById("competition");
const nameField = document.getElementById("reg-name");
const blockField = document.getElementById("reg-block");
const flatField = document.getElementById("reg-flat");
const mobileField = document.getElementById("reg-mobile");
const ageField = document.getElementById("reg-age");

// ======================================
// Cultural Programs Registration Modal
// ======================================

const culturalCard = document.getElementById("cultural-programs");

const culturalModal = document.getElementById("cultural-registration-modal");

const closeCulturalModal = document.getElementById("close-cultural-modal");

const culturalRegisterSubmitBtn = document.getElementById("cultural-register-submit");

const culturalNameField = document.getElementById("cultural-reg-name");
const culturalBlockField = document.getElementById("cultural-reg-block");
const culturalFlatField = document.getElementById("cultural-reg-flat");
const culturalMobileField = document.getElementById("cultural-reg-mobile");
const culturalOtherCheckbox = document.getElementById("cultural-other-checkbox");
const culturalOtherDetailsField = document.getElementById("cultural-other-details");
const culturalTrackField = document.getElementById("cultural-reg-track");

// "Other" category still requires details to be filled in,
// but the field itself is always visible now (not just for
// "Other") so residents can add a distinguishing note (e.g.
// song title) for any category if they want to.


// ======================================
// Volunteer Registration Modal
// ======================================

const volunteerCard = document.getElementById("volunteer");

const volunteerModal = document.getElementById("volunteer-registration-modal");

const closeVolunteerModal = document.getElementById("close-volunteer-modal");

const volunteerRegisterSubmitBtn = document.getElementById("volunteer-register-submit");

const volunteerNameField = document.getElementById("volunteer-reg-name");
const volunteerBlockField = document.getElementById("volunteer-reg-block");
const volunteerFlatField = document.getElementById("volunteer-reg-flat");
const volunteerMobileField = document.getElementById("volunteer-reg-mobile");
const volunteerOtherCheckbox = document.getElementById("volunteer-other-checkbox");
const volunteerOtherDetailsField = document.getElementById("volunteer-other-details");

// Show/hide the "Other" details text field based on checkbox state
volunteerOtherCheckbox.addEventListener("change", function () {

    volunteerOtherDetailsField.style.display = volunteerOtherCheckbox.checked ? "block" : "none";

    if (!volunteerOtherCheckbox.checked) {
        volunteerOtherDetailsField.value = "";
    }

});

// ======================================
// Send Button
// ======================================

sendButton.addEventListener("click", function () {

    if (!sendButton.disabled) {
        sendMessage();
    }

});

userInput.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {

        event.preventDefault();

        if (!sendButton.disabled) {
            sendMessage();
        }

    }

});

// ======================================
// Quick Registration Popup
// ======================================

quickRegisterCard.addEventListener("click", function () {

    registrationChoiceModal.style.display = "block";

}); 

registerByForm.addEventListener("click", function () {

    registrationChoiceModal.style.display = "none";

    // Open your existing Quick Registration form
    registrationModal.style.display = "block";

});


registerByChat.addEventListener("click", function () {

    registrationChoiceModal.style.display = "none";

    // Move to the existing chatbot
    chatContainer.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    // Make sure the chatbot is ready to send
     sendButton.disabled = false;
    // Trigger exactly the same action
    // as the user manually typing "register"
    // Put "register" into the chatbot
    // Use the existing chatbot flow
    userInput.value = "register";
    sendMessage();
    
});


closeRegistrationChoice.addEventListener("click", function () {

    registrationChoiceModal.style.display = "none";

});


cancelRegistrationChoice.addEventListener("click", function () {

    registrationChoiceModal.style.display = "none";

});


closeModal.addEventListener("click", function () {

    registrationModal.style.display = "none";

});

window.addEventListener("click", function (event) {

    if (event.target === registrationModal) {

        registrationModal.style.display = "none";

    }

    if (event.target === culturalModal) {

        culturalModal.style.display = "none";

    }

    if (event.target === volunteerModal) {

        volunteerModal.style.display = "none";

    }

});

// ======================================
// Cultural Programs Popup
// ======================================

culturalCard.addEventListener("click", function () {

    culturalModal.style.display = "block";

});

closeCulturalModal.addEventListener("click", function () {

    culturalModal.style.display = "none";

});

// ======================================
// Volunteer Popup
// ======================================

volunteerCard.addEventListener("click", function () {

    volunteerModal.style.display = "block";

});

closeVolunteerModal.addEventListener("click", function () {

    volunteerModal.style.display = "none";

});

registerSubmitBtn.addEventListener("click", async function () {

    const registrationData = {
        competition: competitionField.value,
        name: nameField.value.trim(),
        block: blockField.value,
        flat: flatField.value.trim(),
        mobile: mobileField.value.trim(),
        age: ageField.value.trim()
    };

    // -----------------------------
    // Basic validation
    // -----------------------------
    if (registrationData.name === "") {
        alert("Please enter your name.");
        nameField.focus();
        return;
    }

    if (registrationData.flat === "") {
        alert("Please enter your flat number.");
        flatField.focus();
        return;
    }

    if (!/^[0-9]{10}$/.test(registrationData.mobile)) {
        alert("Please enter a valid 10-digit mobile number.");
        mobileField.focus();
        return;
    }

    const ageValue = Number(registrationData.age);

    if (registrationData.age === "" || isNaN(ageValue) || ageValue < 1 || ageValue > 100) {
        alert("Please enter a valid age between 1 and 100.");
        ageField.focus();
        return;
    }

    registerSubmitBtn.disabled = true;
    registerSubmitBtn.innerHTML = "Registering...";

    try {

        const response = await fetch("/register", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(registrationData)

        });

        const responseData = await response.json();

        if (!response.ok) {

            // Show the specific validation message from the server
            // (e.g. invalid flat number for the selected block)
            const errorMessage = responseData.detail || "Registration failed. Please check your details.";
            alert("⚠️ " + errorMessage);
            return;

        }

        showThankYouPopup(registrationData.name);

        // Reset form and close modal
        nameField.value = "";
        flatField.value = "";
        mobileField.value = "";
        ageField.value = "";
        competitionField.selectedIndex = 0;
        blockField.selectedIndex = 0;

        registrationModal.style.display = "none";

    }
    catch (error) {

        console.error(error);
        alert("⚠️ Unable to submit registration. Please check your connection and try again.");

    }
    finally {

        registerSubmitBtn.disabled = false;
        registerSubmitBtn.innerHTML = "Register";

    }

});

// ======================================
// Cultural Programs Registration Submit
// ======================================

culturalRegisterSubmitBtn.addEventListener("click", async function () {

    const selectedCategories = Array.from(
        document.querySelectorAll(".cultural-category:checked")
    ).map(function (checkbox) {
        return checkbox.value;
    });

    if (selectedCategories.length === 0) {
        alert("Please select at least one category.");
        return;
    }

    const name = culturalNameField.value.trim();
    const block = culturalBlockField.value;
    const flat = culturalFlatField.value.trim();
    const mobile = culturalMobileField.value.trim();
    const otherDetails = culturalOtherDetailsField.value.trim();

    // -----------------------------
    // Basic validation
    // -----------------------------
    if (name === "") {
        alert("Please enter your name.");
        culturalNameField.focus();
        return;
    }

    if (flat === "") {
        alert("Please enter your flat number.");
        culturalFlatField.focus();
        return;
    }

    if (!/^[0-9]{10}$/.test(mobile)) {
        alert("Please enter a valid 10-digit mobile number.");
        culturalMobileField.focus();
        return;
    }

    if (culturalOtherCheckbox.checked && otherDetails === "") {
        alert("Please specify details for 'Other'.");
        culturalOtherDetailsField.focus();
        return;
    }

    const trackFile = culturalTrackField.files.length > 0 ? culturalTrackField.files[0] : null;

    const trackFileName = trackFile ? trackFile.name.toLowerCase() : "";
    const isValidTrackFormat = trackFileName.endsWith(".mp3") || trackFileName.endsWith(".m4a");

    if (trackFile && !isValidTrackFormat) {
        alert("Please upload only .mp3 or .m4a files for the performance track.");
        return;
    }

    culturalRegisterSubmitBtn.disabled = true;
    culturalRegisterSubmitBtn.innerHTML = "Registering...";

    try {

        // FormData is used instead of JSON since this request
        // may include a binary file (the mp3 track).
        const formData = new FormData();
        formData.append("name", name);
        formData.append("block", block);
        formData.append("flat", flat);
        formData.append("mobile", mobile);
        formData.append("categories", selectedCategories.join(", "));
        formData.append("other_details", otherDetails);

        if (trackFile) {
            formData.append("track", trackFile);
        }

        const response = await fetch("/register-cultural", {

            method: "POST",

            body: formData

            // No Content-Type header here - the browser sets the
            // correct multipart boundary automatically for FormData.

        });

        const responseData = await response.json();

        if (!response.ok) {

            const errorMessage = responseData.detail || "Registration failed. Please check your details.";
            alert("⚠️ " + errorMessage);
            return;

        }

        showThankYouPopup(name);

        // Reset form and close modal
        document.querySelectorAll(".cultural-category:checked").forEach(function (checkbox) {
            checkbox.checked = false;
        });
        culturalNameField.value = "";
        culturalFlatField.value = "";
        culturalMobileField.value = "";
        culturalOtherDetailsField.value = "";
        culturalTrackField.value = "";
        culturalBlockField.selectedIndex = 0;

        culturalModal.style.display = "none";

    }
    catch (error) {

        console.error(error);
        alert("⚠️ Unable to submit registration. Please check your connection and try again.");

    }
    finally {

        culturalRegisterSubmitBtn.disabled = false;
        culturalRegisterSubmitBtn.innerHTML = "Register";

    }

});

// ======================================
// Volunteer Registration Submit
// ======================================

volunteerRegisterSubmitBtn.addEventListener("click", async function () {

    const selectedTasks = Array.from(
        document.querySelectorAll(".volunteer-task:checked")
    ).map(function (checkbox) {
        return checkbox.value;
    });

    if (selectedTasks.length === 0) {
        alert("Please select at least one task.");
        return;
    }

    const volunteerData = {
        tasks: selectedTasks.join(", "),
        name: volunteerNameField.value.trim(),
        block: volunteerBlockField.value,
        flat: volunteerFlatField.value.trim(),
        mobile: volunteerMobileField.value.trim(),
        other_details: volunteerOtherDetailsField.value.trim()
    };

    // -----------------------------
    // Basic validation
    // -----------------------------
    if (volunteerData.name === "") {
        alert("Please enter your name.");
        volunteerNameField.focus();
        return;
    }

    if (volunteerData.flat === "") {
        alert("Please enter your flat number.");
        volunteerFlatField.focus();
        return;
    }

    if (!/^[0-9]{10}$/.test(volunteerData.mobile)) {
        alert("Please enter a valid 10-digit mobile number.");
        volunteerMobileField.focus();
        return;
    }

    if (volunteerOtherCheckbox.checked && volunteerData.other_details === "") {
        alert("Please specify details for 'Other'.");
        volunteerOtherDetailsField.focus();
        return;
    }

    volunteerRegisterSubmitBtn.disabled = true;
    volunteerRegisterSubmitBtn.innerHTML = "Registering...";

    try {

        const response = await fetch("/register-volunteer", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(volunteerData)

        });

        const responseData = await response.json();

        if (!response.ok) {

            const errorMessage = responseData.detail || "Registration failed. Please check your details.";
            alert("⚠️ " + errorMessage);
            return;

        }

        showThankYouPopup(volunteerData.name);

        // Reset form and close modal
        document.querySelectorAll(".volunteer-task:checked").forEach(function (checkbox) {
            checkbox.checked = false;
        });
        volunteerNameField.value = "";
        volunteerFlatField.value = "";
        volunteerMobileField.value = "";
        volunteerOtherDetailsField.value = "";
        volunteerOtherDetailsField.style.display = "none";
        volunteerBlockField.selectedIndex = 0;

        volunteerModal.style.display = "none";

    }
    catch (error) {

        console.error(error);
        alert("⚠️ Unable to submit registration. Please check your connection and try again.");

    }
    finally {

        volunteerRegisterSubmitBtn.disabled = false;
        volunteerRegisterSubmitBtn.innerHTML = "Register";

    }

});

async function sendMessage() {


    if (sendButton.disabled) {
        return;
    }


    const message = userInput.value.trim();

    console.log("Sending:", message);

    if (message === "") return;

    // Disable button while waiting
    sendButton.disabled = true;
    sendButton.innerHTML = "Sending...";

    // -----------------------------
    // User Message
    // -----------------------------
    chatContainer.innerHTML += `

    <div class="user-message-wrapper">

        <div>

            <div class="user-title">
                You
            </div>

            <div class="user-message">
                ${message}
            </div>

        </div>

    </div>

    `;

    userInput.value = "";

    chatContainer.scrollTop = chatContainer.scrollHeight;

    // -----------------------------
    // Typing Animation
    // -----------------------------
    const typingId = "typing-" + Date.now();

    chatContainer.innerHTML += `

    <div class="bot-message" id="${typingId}" style="margin-top:20px;">

        <div class="avatar">
            <img src="assets/images/app_logo.png" alt="AI">
        </div>

        <div class="message">

            <strong>LVS AI Assistant</strong>

            <div class="typing-box">

                <div class="typing-text">

                    Preparing your answer...

                </div>

                <div class="typing-indicator">

                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>

                </div>

            </div>

        </div>

    </div>

    `;

    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();
        console.log("Backend Response:", data);


        // Remove typing animation
        const typingElement = document.getElementById(typingId);

        if (typingElement) {
            typingElement.remove();
        }

        // -----------------------------
        // AI Response
        // -----------------------------
        chatContainer.innerHTML += `

        <div class="bot-message" style="margin-top:20px;">

            <div class="avatar">

                <img src="assets/images/app_logo.png" alt="AI">

            </div>

            <div class="message">

                <strong>LVS AI Assistant</strong>

                <br><br>

                ${data.response}

            </div>

        </div>

        `;

        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Registration completed via the chatbot flow -
        // show the same Ganesha thank-you popup used for
        // the web-form registrations.
        if (data.popup_name && typeof showThankYouPopup === "function") {
            showThankYouPopup(data.popup_name, data.popup_action);
        }

    }
    catch (error) {

        console.error(error);

        // Remove typing animation
        const typingElement = document.getElementById(typingId);

        if (typingElement) {
            typingElement.remove();
        }

        chatContainer.innerHTML += `

        <div class="bot-message" style="margin-top:20px;">

            <div class="avatar">

                ⚠️

            </div>

            <div class="message">

                Unable to connect to AI Assistant.

            </div>

        </div>

        `;

    }
    finally {

        // Enable button again
        sendButton.disabled = false;
        sendButton.innerHTML = "Send";

        userInput.focus();

    }

}
// ======================================
// Schedule Card Click -> Opens Schedule Modal
// ======================================

const scheduleCard = document.getElementById("schedule");
const scheduleModal = document.getElementById("schedule-modal");
const scheduleModalBody = document.getElementById("schedule-modal-body");
const closeScheduleModal = document.getElementById("close-schedule-modal");
const askAiScheduleBtn = document.getElementById("ask-ai-schedule-btn");

scheduleCard.addEventListener("click", async function () {

    scheduleModal.style.display = "block";
    scheduleModalBody.textContent = "Loading schedule...";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: "full schedule"
            })

        });

        const data = await response.json();

        scheduleModalBody.textContent =
            data.response || "Schedule is not available right now.";

    } catch (error) {

        console.error("Schedule fetch error:", error);

        scheduleModalBody.textContent =
            "Unable to load the schedule right now. Please try again.";

    }

});

closeScheduleModal.addEventListener("click", function () {
    scheduleModal.style.display = "none";
});

// Close when clicking outside the modal content
scheduleModal.addEventListener("click", function (event) {
    if (event.target === scheduleModal) {
        scheduleModal.style.display = "none";
    }
});

// "Ask AI Assistant" -> hand off to chat, let user type freely
// (e.g. "day 2", "when is dance") using existing schedule search logic
askAiScheduleBtn.addEventListener("click", function () {

    scheduleModal.style.display = "none";

    chatContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    userInput.value = "";
    userInput.placeholder = "e.g. \"day 2\", \"when is dance\", \"full schedule\"...";
    userInput.focus();

});

// ======================================
// Annaprasada Card Click
// ======================================

const annaprasadaCard = document.getElementById("annaprasada");

annaprasadaCard.addEventListener("click", function () {

    // Scroll to chat section smoothly
    chatContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    // Auto-fill and send the message
    userInput.value = "annaprasada";

    sendMessage();

});
// ======================================
// Donation Card Click
// ======================================

const donationCard = document.getElementById("donation");

donationCard.addEventListener("click", function () {

    chatContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    userInput.value = "donation";

    sendMessage();

});

// ======================================
// Donation Payment Proof — Enable/Submit
// ======================================

function enableDonationSubmit(inputElement) {

    const submitBtn = document.getElementById("donation-submit-btn");

    if (!submitBtn) return;

    if (inputElement.files && inputElement.files.length > 0) {

        submitBtn.disabled = false;
        submitBtn.style.background = "#4CAF50";
        submitBtn.style.cursor = "pointer";

    } else {

        submitBtn.disabled = true;
        submitBtn.style.background = "#ccc";
        submitBtn.style.cursor = "not-allowed";

    }

}

function submitDonationProof() {

    const inputElement = document.getElementById("donation-proof-input");

    if (!inputElement || !inputElement.files || inputElement.files.length === 0) {
        return;
    }

    uploadDonationProof(inputElement);

}

// ======================================
// Donation Payment Proof Screenshot Upload
// ======================================

async function uploadDonationProof(inputElement) {

    if (!inputElement.files || inputElement.files.length === 0) {
        return;
    }

    const file = inputElement.files[0];

    // -----------------------------
    // User Message (screenshot preview)
    // -----------------------------
    const previewUrl = URL.createObjectURL(file);

    chatContainer.innerHTML += `

    <div class="user-message-wrapper">

        <div>

            <div class="user-title">
                You
            </div>

            <div class="user-message">
                📷 Uploaded payment screenshot
                <br>
                <img src="${previewUrl}" style="width:140px;border-radius:10px;margin-top:8px;">
            </div>

        </div>

    </div>

    `;

    chatContainer.scrollTop = chatContainer.scrollHeight;

    // -----------------------------
    // Typing Animation
    // -----------------------------
    const typingId = "typing-" + Date.now();

    chatContainer.innerHTML += `

    <div class="bot-message" id="${typingId}" style="margin-top:20px;">

        <div class="avatar">
            <img src="assets/images/app_logo.png" alt="AI">
        </div>

        <div class="message">

            <strong>LVS AI Assistant</strong>

            <div class="typing-box">

                <div class="typing-text">
                    Verifying your screenshot...
                </div>

                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>

            </div>

        </div>

    </div>

    `;

    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {

        const formData = new FormData();
        formData.append("proof", file);

        const response = await fetch("/donation/upload-proof", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }

        if (!response.ok) {

            chatContainer.innerHTML += `

            <div class="bot-message" style="margin-top:20px;">

                <div class="avatar">⚠️</div>

                <div class="message">
                    ${data.detail || "Unable to process this screenshot. Please try again."}
                </div>

            </div>

            `;

        } else {

            chatContainer.innerHTML += `

            <div class="bot-message" style="margin-top:20px;">

                <div class="avatar">
                    <img src="assets/images/app_logo.png" alt="AI">
                </div>

                <div class="message">

                    <strong>LVS AI Assistant</strong>

                    <br><br>

                    ${data.response}

                </div>

            </div>

            `;

        }

        chatContainer.scrollTop = chatContainer.scrollHeight;

        if (data.popup_name && typeof showThankYouPopup === "function") {
            showThankYouPopup(data.popup_name, data.popup_action);
        }

    } catch (error) {

        console.error("Donation proof upload error:", error);

        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }

        chatContainer.innerHTML += `

        <div class="bot-message" style="margin-top:20px;">

            <div class="avatar">⚠️</div>

            <div class="message">
                Unable to upload the screenshot right now. Please check your connection and try again.
            </div>

        </div>

        `;

        chatContainer.scrollTop = chatContainer.scrollHeight;

    }

    // Reset the file input so the same file can be re-selected if needed
    inputElement.value = "";

}

// ======================================
// PWA: Register Service Worker
// ======================================
// Enables "Add to Home Screen" on Android/Chrome/iOS.
// Safe to fail silently on older browsers or if the
// site isn't served over HTTPS yet (e.g. plain ngrok
// http during local dev).

if ("serviceWorker" in navigator) {

    window.addEventListener("load", function () {

        navigator.serviceWorker
            .register("/sw.js")
            .then(function () {

                // Check whether this device already has an
                // active push subscription from a previous
                // visit - without this, the button always
                // resets to "Enable Festival Alerts" on
                // every page load, even after successfully
                // subscribing before.
                return navigator.serviceWorker.ready;

            })
            .then(function (registration) {

                return registration.pushManager.getSubscription();

            })
            .then(function (existingSubscription) {

                const button = document.getElementById("enable-notifications-btn");

                if (existingSubscription && button) {
                    button.textContent = "✅ Alerts Enabled";
                    button.disabled = true;
                    button.style.opacity = "0.7";
                }

            })
            .catch(function (error) {
                console.log("Service worker registration failed:", error);
            });

    });

}

// ======================================
// Push Notifications
// ======================================
// Converts the VAPID public key (base64 URL-safe string
// from the backend) into the Uint8Array format the Push
// API requires.

function urlBase64ToUint8Array(base64String) {

    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
}

function enableNotifications() {

    const button = document.getElementById("enable-notifications-btn");

    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        alert("Notifications aren't supported on this browser/device.");
        return;
    }

    Notification.requestPermission().then(function (permission) {

        if (permission !== "granted") {
            alert("Notification permission was not granted.");
            return;
        }

        navigator.serviceWorker.ready.then(function (registration) {

            fetch("/api/vapid-public-key")
                .then(function (response) { return response.json(); })
                .then(function (data) {

                    const applicationServerKey = urlBase64ToUint8Array(data.public_key);

                    return registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: applicationServerKey
                    });

                })
                .then(function (subscription) {

                    return fetch("/api/push-subscribe", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(subscription.toJSON())
                    });

                })
                .then(function () {

                    if (button) {
                        button.textContent = "✅ Alerts Enabled";
                        button.disabled = true;
                        button.style.opacity = "0.7";
                    }

                })
                .catch(function (error) {
                    console.log("Push subscription failed:", error);
                    alert("Could not enable notifications. Please try again.");
                });

        });

    });

}

// ======================================
// Announcements Banner
// ======================================
// Polls the backend periodically so new announcements
// appear on screen without needing to reload the page -
// this covers residents who have the app/tab open but
// haven't enabled push notifications.

function loadAnnouncements() {

    fetch("/api/announcements")
        .then(function (response) { return response.json(); })
        .then(function (data) {

            const banner = document.getElementById("announcements-banner");

            if (!banner) return;

            const announcements = data.announcements || [];

            if (announcements.length === 0) {
                banner.style.display = "none";
                banner.classList.remove("has-urgent");
                banner.innerHTML = "";
                return;
            }

            const hasUrgent = announcements.some(function (a) {
                return a.type === "urgent";
            });

            const hasReminder = announcements.some(function (a) {
                return a.type === "reminder";
            });

            // Urgent takes priority for the overall banner color
            // if a mix of types is active at once.
            banner.classList.toggle("has-urgent", hasUrgent);
            banner.classList.toggle("has-reminder", !hasUrgent && hasReminder);

            const tickerItems = announcements.map(function (announcement) {

                let icon = "📢";
                if (announcement.type === "urgent") icon = "🚨";
                else if (announcement.type === "reminder") icon = "🔔";

                return (
                    '<span class="ticker-item">' +
                    icon + " " + announcement.message +
                    "</span>"
                );

            }).join("");

            // Duplicate the items so the scroll loops seamlessly
            // without a visible gap/jump when it wraps around.
            banner.innerHTML =
                '<div class="ticker-track">' + tickerItems + tickerItems + '</div>';

            banner.style.display = "block";

        })
        .catch(function () {
            // Silently ignore - announcements are a nice-to-have,
            // not critical to the rest of the app working.
        });

}

document.addEventListener("DOMContentLoaded", function () {

    loadAnnouncements();

    // Poll every 60 seconds for new announcements while
    // the app is open.
    setInterval(loadAnnouncements, 60000);

});

// ======================================
// Registration Thank You Popup
// ======================================
// Shown after any successful registration (competition,
// cultural, volunteer) instead of a plain browser alert() -
// same Ganesha branding used for the chatbot, for a
// consistent, warmer confirmation experience.

const thankYouModal = document.getElementById("thank-you-modal");
const thankYouMessage = document.getElementById("thank-you-message");
const closeThankYouModal = document.getElementById("close-thank-you-modal");
const thankYouOkBtn = document.getElementById("thank-you-ok-btn");

function showThankYouPopup(name, action) {

    const displayName = name && name.trim() ? name.trim() : "there";
    const actionText = action || "registering";

    thankYouMessage.textContent =
        "Hey " + displayName + ", thanks for " + actionText + "!";

    thankYouModal.style.display = "block";

}

function hideThankYouPopup() {
    thankYouModal.style.display = "none";
}

if (closeThankYouModal) {
    closeThankYouModal.addEventListener("click", hideThankYouPopup);
}

if (thankYouOkBtn) {
    thankYouOkBtn.addEventListener("click", hideThankYouPopup);
}

if (thankYouModal) {

    thankYouModal.addEventListener("click", function (event) {

        // Close if the dark overlay itself is clicked,
        // not the card inside it.
        if (event.target === thankYouModal) {
            hideThankYouPopup();
        }

    });

}