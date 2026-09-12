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
// Competition/Game Registration status
// ======================================
// Mirrors backend/config.py's COMPETITION_REGISTRATIONS_OPEN.
// Defaults to true so the card isn't wrongly blocked while the
// status fetch below is still in flight; the server is the real
// gatekeeper regardless (see /register in main.py).

let competitionRegistrationsOpen = true;

fetch("/registration-status")
    .then(function (response) { return response.json(); })
    .then(function (data) {
        competitionRegistrationsOpen = data.competition_registrations_open;
    })
    .catch(function (error) {
        console.log("Could not load registration status:", error);
    });

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

// ===== Cultural Registration: auto-fill for a returning resident =====
let culturalLastLookedUpMobile = "";

async function lookupCulturalResident() {
    if (!culturalMobileField) return;

    const mobile = culturalMobileField.value.trim();

    if (!/^\d{10}$/.test(mobile) || mobile === culturalLastLookedUpMobile) {
        return;
    }

    culturalLastLookedUpMobile = mobile;

    try {
        const res = await fetch("/api/lookup-resident/" + encodeURIComponent(mobile));
        const data = await res.json();

        if (data.found) {
            if (culturalNameField && !culturalNameField.value) culturalNameField.value = data.name;
            if (culturalBlockField && !culturalBlockField.value) culturalBlockField.value = data.block;
            if (culturalFlatField && !culturalFlatField.value) culturalFlatField.value = data.flat_number;
        }
    } catch (err) {
        // Silent failure - this is a convenience, not a required step.
    }
}

if (culturalMobileField) {
    culturalMobileField.addEventListener("input", lookupCulturalResident);
    culturalMobileField.addEventListener("blur", lookupCulturalResident);
}
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

// ===== Volunteer Registration: auto-fill for a returning resident =====
let volunteerLastLookedUpMobile = "";

async function lookupVolunteerResident() {
    if (!volunteerMobileField) return;

    const mobile = volunteerMobileField.value.trim();

    if (!/^\d{10}$/.test(mobile) || mobile === volunteerLastLookedUpMobile) {
        return;
    }

    volunteerLastLookedUpMobile = mobile;

    try {
        const res = await fetch("/api/lookup-resident/" + encodeURIComponent(mobile));
        const data = await res.json();

        if (data.found) {
            if (volunteerNameField && !volunteerNameField.value) volunteerNameField.value = data.name;
            if (volunteerBlockField && !volunteerBlockField.value) volunteerBlockField.value = data.block;
            if (volunteerFlatField && !volunteerFlatField.value) volunteerFlatField.value = data.flat_number;
        }
    } catch (err) {
        // Silent failure - this is a convenience, not a required step.
    }
}

if (volunteerMobileField) {
    volunteerMobileField.addEventListener("input", lookupVolunteerResident);
    volunteerMobileField.addEventListener("blur", lookupVolunteerResident);
}

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

    if (!competitionRegistrationsOpen) {

        alert(
            "🚫 Competition/game registrations are now closed for " +
            "this festival. If this is a mistake, please contact a volunteer."
        );

        return;

    }

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
    const isValidTrackFormat = trackFileName.endsWith(".mp3");

    if (trackFile && !isValidTrackFormat) {
        alert("Please upload only .mp3 files for the performance track.");
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
        mobile: volunteerMobileField.value.trim()
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
        const speechSafeText = data.response
            .replace(/<[^>]*>/g, " ")   // strip HTML tags before reading aloud
            .replace(/[🙏🪔🎉🏆👤🏢🏠📱💰🔎🧾⏳📥✅❌📆🕒📍🎂👥🎟️👋1️⃣2️⃣3️⃣]/g, "");

        const speakId = "speak-" + Date.now();

        chatContainer.innerHTML += `

        <div class="bot-message" style="margin-top:20px;">

            <div class="avatar">

                <img src="assets/images/app_logo.png" alt="AI">

            </div>

            <div class="message">

                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                    <strong>LVS AI Assistant</strong>
                    <button
                        type="button"
                        onclick="speakText(this, ${JSON.stringify(speechSafeText)})"
                        title="Listen to this answer"
                        style="background:none;border:none;font-size:18px;cursor:pointer;flex-shrink:0;">
                        🔊
                    </button>
                </div>

                <br>

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

    // Find the submit button that belongs to THIS specific
    // donation message, not just the first one with this ID
    // anywhere on the page. Since donation messages can be
    // shown more than once in the same chat session (e.g. a
    // second donation for a different family member), using
    // getElementById alone would always grab the very first
    // one ever rendered, even if it's from an earlier,
    // already-completed donation. Walking up to the shared
    // container and querying within it scopes the lookup to
    // just this message's own button.
    const container = inputElement.closest(".message, .bot-message, div");

    let submitBtn = container
        ? container.querySelector(".donation-submit-btn")
        : null;

    // Fallback for older messages rendered before this fix,
    // which may still use the plain ID-based button.
    if (!submitBtn) {
        submitBtn = document.getElementById("donation-submit-btn");
    }

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

function submitDonationProof(buttonElement) {

    // Same scoping fix as enableDonationSubmit above - find
    // the file input that belongs to THIS message's button,
    // not just the first "donation-proof-input" on the page.
    let inputElement = null;

    if (buttonElement) {

        const container = buttonElement.closest(".message, .bot-message, div");

        inputElement = container
            ? container.querySelector(".donation-proof-input")
            : null;
    }

    // Fallback for older messages rendered before this fix.
    if (!inputElement) {
        inputElement = document.getElementById("donation-proof-input");
    }

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

                _setNotificationButtonsEnabled(!!existingSubscription);

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

// Keeps the hero "Enable Festival Alerts" button and the
// top-right bell icon in sync with each other - there are
// two entry points to the same action, so both need to
// reflect the same enabled/disabled state.
function _setNotificationButtonsEnabled(isEnabled) {

    const heroButton = document.getElementById("enable-notifications-btn");
    const bellButton = document.getElementById("bell-notifications-btn");

    if (isEnabled) {

        if (heroButton) {
            heroButton.textContent = "✅ Alerts Enabled";
            heroButton.disabled = true;
            heroButton.style.opacity = "0.7";
        }

        if (bellButton) {
            bellButton.classList.add("alerts-enabled");
            bellButton.title = "Festival alerts enabled";
        }

    }

}

function enableNotifications() {

    const bellButton = document.getElementById("bell-notifications-btn");

    if (bellButton && bellButton.classList.contains("alerts-enabled")) {
        alert("✅ Festival alerts are already enabled on this device.");
        return;
    }

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

                    _setNotificationButtonsEnabled(true);

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

            const tickerItems = announcements.map(function (announcement) {

                let icon = "📢";
                let typeClass = "type-info";

                if (announcement.type === "urgent") {
                    icon = "🚨";
                    typeClass = "type-urgent";
                } else if (announcement.type === "reminder") {
                    icon = "🔔";
                    typeClass = "type-reminder";
                }

                return (
                    '<span class="ticker-item ' + typeClass + '">' +
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

// ======================================
// Floating WhatsApp Share Button
// ======================================
// Uses window.location.origin so this always points at
// whatever domain the app is actually running on (ngrok
// during dev, or the real production domain later) without
// needing any hardcoded URL.

const whatsappShareBtn = document.getElementById("whatsapp-share-btn");

if (whatsappShareBtn) {

    whatsappShareBtn.addEventListener("click", function (event) {

        event.preventDefault();

        const appUrl = window.location.origin;

        const shareMessage =
            "🙏 Check out the LVS Excellency Ganesha Festival App! 🎉\n\n" +
            "Schedule, registrations, donations, Annaprasada booking and more, all in one place:\n" +
            appUrl;

        const whatsappUrl =
            "https://wa.me/?text=" + encodeURIComponent(shareMessage);

        window.open(whatsappUrl, "_blank");

    });

}

// ======================================
// Install App (Add to Home Screen)
// ======================================
// Chrome/Android fires "beforeinstallprompt" when the app
// is installable - we capture that event and hold onto it,
// since the browser only allows triggering install() in
// response to an actual user gesture (our button click),
// not automatically. iOS Safari does NOT support this
// event at all (Apple has no programmatic install API), so
// on iOS the button just shows manual instructions instead.

let deferredInstallPrompt = null;

const installAppBtn = document.getElementById("install-app-btn");

window.addEventListener("beforeinstallprompt", function (event) {

    event.preventDefault();
    deferredInstallPrompt = event;

});

window.addEventListener("appinstalled", function () {

    deferredInstallPrompt = null;

    if (installAppBtn) {
        installAppBtn.classList.add("app-installed");
    }

});

function _isIOSDevice() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
}

if (installAppBtn) {

    installAppBtn.addEventListener("click", function () {

        if (deferredInstallPrompt) {

            deferredInstallPrompt.prompt();

            deferredInstallPrompt.userChoice.then(function () {
                deferredInstallPrompt = null;
            });

        } else if (_isIOSDevice()) {

            alert(
                "To install this app on your iPhone/iPad:\n\n" +
                "1. Tap the Share button (square with an arrow) in Safari\n" +
                "2. Scroll down and tap \"Add to Home Screen\"\n" +
                "3. Tap \"Add\""
            );

        } else {

            alert(
                "This app may already be installed - check your home " +
                "screen, or look for \"Open in app\" / an install icon " +
                "in your browser's address bar.\n\n" +
                "If not installed yet, look in your browser's menu for " +
                "\"Install app\" or \"Add to Home Screen\"."
            );

        }

    });

}
// ======================================
// Opening Mantra
// ======================================
// Browsers block audio-with-sound autoplay on page load
// for anyone who hasn't already interacted with the site -
// this is a deliberate, universal browser policy, not
// something we can code around. So this tries to autoplay
// (works for some return visits), and gracefully falls
// back to a small tap-to-play prompt if the browser blocks
// it - nothing silently fails without the resident knowing.

document.addEventListener("DOMContentLoaded", function () {

    const mantraAudio = document.getElementById("mantra-audio");
    const mantraPrompt = document.getElementById("mantra-tap-prompt");
    const mantraTapBtn = document.getElementById("mantra-tap-btn");

    if (!mantraAudio) return;

    const playPromise = mantraAudio.play();

    if (playPromise !== undefined) {

        playPromise.catch(function () {

            // Autoplay was blocked - show the tap prompt instead.
            if (mantraPrompt) {
                mantraPrompt.style.display = "block";
            }

        });

    }

    if (mantraTapBtn) {

        mantraTapBtn.addEventListener("click", function () {

            mantraAudio.play();
            mantraPrompt.style.display = "none";

        });

    }

});

/* ==========================================
   VOICE INPUT (Speech-to-Text)
========================================== */
// Uses the browser's built-in Web Speech API - no
// server calls, no API costs, works entirely on-device.
// Supported well on Chrome/Edge (desktop + Android).
// Safari/iOS support is limited, so the mic button is
// hidden entirely there rather than showing something
// that silently fails.

let voiceRecognition = null;
let isListening = false;

function initVoiceRecognition() {

    const SpeechRecognitionAPI =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    const micBtn = document.getElementById("mic-btn");

    if (!SpeechRecognitionAPI) {
        // Not supported on this browser (e.g. Safari/iOS) -
        // hide the mic button entirely rather than showing
        // something that won't work.
        if (micBtn) micBtn.style.display = "none";
        return;
    }

    voiceRecognition = new SpeechRecognitionAPI();
    voiceRecognition.lang = "en-IN";
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = false;

    voiceRecognition.onresult = function (event) {

        const transcript = event.results[0][0].transcript;

        // Fills the text box for the resident to review/edit
        // before sending - not auto-sent, since a misheard
        // word (e.g. a flat number) could otherwise submit
        // wrong data without them noticing.
        userInput.value = transcript;
        userInput.focus();
    };

    voiceRecognition.onerror = function () {
        stopListeningUI();
    };

    voiceRecognition.onend = function () {
        stopListeningUI();
    };
}

function stopListeningUI() {

    isListening = false;

    const micBtn = document.getElementById("mic-btn");

    if (micBtn) {
        micBtn.style.background = "#1976d2";
        micBtn.innerHTML = "🎤";
    }
}

function toggleVoiceInput() {

    if (!voiceRecognition) {
        initVoiceRecognition();
    }

    if (!voiceRecognition) {
        // Still not available after init attempt - browser
        // doesn't support it.
        return;
    }

    const micBtn = document.getElementById("mic-btn");

    if (isListening) {

        voiceRecognition.stop();
        stopListeningUI();
        return;
    }

    isListening = true;

    if (micBtn) {
        micBtn.style.background = "#c62828";
        micBtn.innerHTML = "⏹";
    }

    try {
        voiceRecognition.start();
    } catch (error) {
        // start() throws if called while already running -
        // safe to ignore, onend will reset the UI shortly.
        console.warn("Voice recognition start error:", error);
    }
}

// Set up on page load so the mic button is hidden early
// if unsupported, rather than flashing visible then hiding.
document.addEventListener("DOMContentLoaded", initVoiceRecognition);


/* ==========================================
   VOICE OUTPUT (Text-to-Speech)
========================================== */
// Uses the browser's built-in speechSynthesis API - same
// no-cost, on-device approach as voice input above.

let currentSpeechUtterance = null;

function speakText(buttonElement, text) {

    if (!window.speechSynthesis) {
        // Not supported on this browser - silently do
        // nothing rather than showing a broken button.
        return;
    }

    // If this exact button is already speaking, tapping it
    // again stops playback instead of restarting it.
    if (currentSpeechUtterance && buttonElement.dataset.speaking === "true") {

        window.speechSynthesis.cancel();
        buttonElement.dataset.speaking = "false";
        buttonElement.innerHTML = "🔊";
        currentSpeechUtterance = null;
        return;
    }

    // Stop any other response currently being read aloud,
    // so only one plays at a time.
    window.speechSynthesis.cancel();

    document.querySelectorAll("[data-speaking='true']").forEach(function (btn) {
        btn.dataset.speaking = "false";
        btn.innerHTML = "🔊";
    });

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 0.95;

    utterance.onend = function () {
        buttonElement.dataset.speaking = "false";
        buttonElement.innerHTML = "🔊";
        currentSpeechUtterance = null;
    };

    utterance.onerror = function () {
        buttonElement.dataset.speaking = "false";
        buttonElement.innerHTML = "🔊";
        currentSpeechUtterance = null;
    };

    buttonElement.dataset.speaking = "true";
    buttonElement.innerHTML = "⏸";
    currentSpeechUtterance = utterance;

    window.speechSynthesis.speak(utterance);
}

// ======================================
// Daily Prasadam Section
// ======================================
// Same polling pattern as the announcements banner above -
// keeps the home page's Daily Prasadam section current
// without needing a page reload.

// How long (in minutes) after the last time mentioned in an
// entry's "Distribution Time" text it should keep showing on
// the home page before disappearing on its own. A date in the
// past (before today) is always hidden regardless of this.
const PRASADAM_HIDE_BUFFER_MINUTES = 60;

// Pulls the LAST "H:MM AM/PM" occurrence out of a distribution
// time string (handles both a single time like "8:30 AM
// onwards" and a range like "8:30 AM - 9:30 AM", using the end
// of the range in the range case). Returns null if nothing
// parseable is found, so callers can fall back to showing the
// entry for the whole day rather than guessing wrong.
function parseLastTimeFromText(text) {

    if (!text) return null;

    const matches = Array.from(text.matchAll(/(\d{1,2}):(\d{2})\s*([APap][Mm])/g));

    if (matches.length === 0) return null;

    const last = matches[matches.length - 1];

    let hour = parseInt(last[1], 10);
    const minute = parseInt(last[2], 10);
    const meridiem = last[3].toUpperCase();

    if (meridiem === "PM" && hour !== 12) hour += 12;
    if (meridiem === "AM" && hour === 12) hour = 0;

    return { hour: hour, minute: minute };

}

function loadDailyPrasadam() {

    fetch("/api/daily-prasadam")
        .then(function (response) { return response.json(); })
        .then(function (data) {

            const container = document.getElementById("daily-prasadam-list");

            if (!container) return;

            const now = new Date();
            const todayString = now.toISOString().slice(0, 10);

            // Only keep entries that are still relevant: a future
            // date always shows, a past date never shows, and
            // today's entry disappears once its listed time (plus
            // the buffer above) has passed - if no time could be
            // parsed from the free-text field, it stays visible
            // for the rest of the day rather than guessing wrong.
            const entries = (data.entries || []).filter(function (entry) {

                if (!entry.date) return true;

                if (entry.date > todayString) return true;

                if (entry.date < todayString) return false;

                const parsedTime = parseLastTimeFromText(entry.time_slot);

                if (!parsedTime) return true;

                const hideAt = new Date(entry.date + "T00:00:00");
                hideAt.setHours(parsedTime.hour, parsedTime.minute, 0, 0);
                hideAt.setMinutes(hideAt.getMinutes() + PRASADAM_HIDE_BUFFER_MINUTES);

                return now < hideAt;

            });

            if (entries.length === 0) {
                container.innerHTML = "<p style='color:#888;text-align:center;'>No prasadam schedule posted yet.</p>";
                return;
            }

            container.innerHTML = entries.map(function (entry) {

                const isToday = entry.date === todayString;

                const timeLine = entry.time_slot
                    ? '<p class="prasadam-time">🕒 ' + entry.time_slot + '</p>'
                    : "";

                const sponsorLine = entry.sponsor
                    ? '<p class="prasadam-sponsor">🙏 Sponsored by ' + entry.sponsor + '</p>'
                    : "";

                const dateLabel = new Date(entry.date + "T00:00:00").toLocaleDateString("en-IN", {
                    weekday: "short",
                    day: "numeric",
                    month: "short"
                });

                return (
                    '<div class="prasadam-card' + (isToday ? ' prasadam-today' : '') + '">' +
                        '<p class="prasadam-date">' + (isToday ? "🌟 Today · " : "") + dateLabel + '</p>' +
                        '<p class="prasadam-items">' + entry.items + '</p>' +
                        timeLine +
                        sponsorLine +
                    '</div>'
                );

            }).join("");

        })
        .catch(function () {
            // Silently ignore - same as announcements, this is
            // a nice-to-have, not critical to the app working.
        });

}

document.addEventListener("DOMContentLoaded", function () {

    loadDailyPrasadam();

    setInterval(loadDailyPrasadam, 60000);

});


// ===== Sponsor a Daily Prasadam =====
// Same modal + submit pattern as the T-shirt order form below,
// posting to the public sponsor-request endpoint. The
// coordinator reviews these in the admin panel before they
// become a published Daily Prasadam entry.

function openSponsorModal() {
    const overlay = document.getElementById("sponsor-modal-overlay");
    if (!overlay) return;
    overlay.style.display = "flex";
}

function closeSponsorModal() {
    const overlay = document.getElementById("sponsor-modal-overlay");
    if (!overlay) return;
    overlay.style.display = "none";
}

async function submitSponsorRequest() {

    const statusEl = document.getElementById("sponsor-request-status");
    const name = document.getElementById("sponsor-name").value.trim();
    const block = document.getElementById("sponsor-block").value;
    const flat = document.getElementById("sponsor-flat").value.trim();
    const mobile = document.getElementById("sponsor-mobile").value.trim();
    const preferredDate = document.getElementById("sponsor-date").value;
    const slot = document.getElementById("sponsor-slot").value;
    const item = document.getElementById("sponsor-item").value.trim();
    const notes = document.getElementById("sponsor-notes").value.trim();

    if (!name || !block || !flat || !mobile || !preferredDate || !slot) {
        statusEl.textContent = "Please fill in all your details.";
        statusEl.style.color = "#c62828";
        return;
    }

    const payload = {
        name: name,
        mobile: mobile,
        block: block,
        flat: flat,
        preferred_date: preferredDate,
        slot: slot,
        item: item,
        notes: notes
    };

    statusEl.textContent = "Submitting...";
    statusEl.style.color = "#888";

    try {

        const res = await fetch("/api/daily-prasadam/sponsor-request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Could not submit your request.");
        }

        statusEl.textContent = "";

        closeSponsorModal();

        if (typeof showThankYouPopup === "function") {
            showThankYouPopup(name, "offering to sponsor Daily Prasadam");
        }

        document.getElementById("sponsor-request-form").reset();

    } catch (err) {
        statusEl.textContent = "❌ " + err.message;
        statusEl.style.color = "#c62828";
    }

}


// ===== Sponsor Request: auto-fill for a returning resident =====
let sponsorLastLookedUpMobile = "";

async function lookupSponsorResident() {
    const mobileInput = document.getElementById("sponsor-mobile");
    if (!mobileInput) return;

    const mobile = mobileInput.value.trim();

    if (!/^\d{10}$/.test(mobile) || mobile === sponsorLastLookedUpMobile) {
        return;
    }

    sponsorLastLookedUpMobile = mobile;

    try {
        const res = await fetch("/api/lookup-resident/" + encodeURIComponent(mobile));
        const data = await res.json();

        if (data.found) {
            const nameEl = document.getElementById("sponsor-name");
            const blockEl = document.getElementById("sponsor-block");
            const flatEl = document.getElementById("sponsor-flat");

            if (nameEl && !nameEl.value) nameEl.value = data.name;
            if (blockEl && !blockEl.value) blockEl.value = data.block;
            if (flatEl && !flatEl.value) flatEl.value = data.flat_number;
        }
    } catch (err) {
        // Silent failure - this is a convenience, not a required step.
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const mobileEl = document.getElementById("sponsor-mobile");
    if (mobileEl) {
        mobileEl.addEventListener("input", lookupSponsorResident);
        mobileEl.addEventListener("blur", lookupSponsorResident);
    }
});


// ===== T-Shirt & Kurti Pre-Booking =====
let tshirtCurrentPrice = 380;
let kurtiCurrentPrice = null;

async function loadTshirtPrice() {
    const priceLine = document.getElementById("tshirt-price-line");
    const kurtiPriceLine = document.getElementById("kurti-price-line");
    if (!priceLine) return;
    try {
        const res = await fetch("/api/tshirt-price");
        const data = await res.json();
        tshirtCurrentPrice = data.tshirt_price;
        kurtiCurrentPrice = data.kurti_price;

        priceLine.textContent = "₹" + tshirtCurrentPrice + " per shirt. Reserve now, pay on pickup.";

        if (kurtiPriceLine) {
            kurtiPriceLine.textContent = kurtiCurrentPrice
                ? "₹" + kurtiCurrentPrice + " per Kurti. Reserve now, pay on pickup."
                : "Price to be announced. Reserve now - amount will be confirmed later.";
        }

        updateTshirtTotal();
    } catch (err) {
        priceLine.textContent = "Could not load price right now.";
    }
}

function updateTshirtTotal() {
    const totalLine = document.getElementById("tshirt-total-line");
    if (!totalLine) return;

    const tshirtQty = tshirtOrderQuantity();
    const kurtiQty = kurtiOrderQuantity();

    const parts = [];

    if (tshirtQty > 0) {
        parts.push(tshirtQty + " T-shirt(s) - ₹" + (tshirtQty * tshirtCurrentPrice));
    }

    if (kurtiQty > 0) {
        parts.push(
            kurtiQty + " Kurti(s) - " + (kurtiCurrentPrice ? ("₹" + (kurtiQty * kurtiCurrentPrice)) : "price TBD")
        );
    }

    totalLine.textContent = parts.length ? ("Total: " + parts.join(" | ")) : "";
}

function tshirtOrderQuantity() {
    const ids = ["tshirt-xs", "tshirt-small", "tshirt-medium", "tshirt-large", "tshirt-xl", "tshirt-xxl"];
    return ids.reduce((sum, id) => {
        const el = document.getElementById(id);
        const val = el ? parseInt(el.value, 10) || 0 : 0;
        return sum + val;
    }, 0);
}

function kurtiOrderQuantity() {
    const ids = ["kurti-xs", "kurti-small", "kurti-medium", "kurti-large", "kurti-xl", "kurti-xxl"];
    return ids.reduce((sum, id) => {
        const el = document.getElementById(id);
        const val = el ? parseInt(el.value, 10) || 0 : 0;
        return sum + val;
    }, 0);
}

async function submitTshirtOrder() {
    const statusEl = document.getElementById("tshirt-order-status");
    const name = document.getElementById("tshirt-name").value.trim();
    const block = document.getElementById("tshirt-block").value;
    const flat = document.getElementById("tshirt-flat").value.trim();
    const mobile = document.getElementById("tshirt-mobile").value.trim();

    const payload = {
        name: name,
        block: block,
        flat: flat,
        mobile: mobile,
        xs: parseInt(document.getElementById("tshirt-xs").value, 10) || 0,
        small: parseInt(document.getElementById("tshirt-small").value, 10) || 0,
        medium: parseInt(document.getElementById("tshirt-medium").value, 10) || 0,
        large: parseInt(document.getElementById("tshirt-large").value, 10) || 0,
        xl: parseInt(document.getElementById("tshirt-xl").value, 10) || 0,
        xxl: parseInt(document.getElementById("tshirt-xxl").value, 10) || 0,
        kurti_xs: parseInt(document.getElementById("kurti-xs").value, 10) || 0,
        kurti_small: parseInt(document.getElementById("kurti-small").value, 10) || 0,
        kurti_medium: parseInt(document.getElementById("kurti-medium").value, 10) || 0,
        kurti_large: parseInt(document.getElementById("kurti-large").value, 10) || 0,
        kurti_xl: parseInt(document.getElementById("kurti-xl").value, 10) || 0,
        kurti_xxl: parseInt(document.getElementById("kurti-xxl").value, 10) || 0
    };

    if (!name || !block || !flat || !mobile) {
        statusEl.textContent = "Please fill in all your details.";
        statusEl.style.color = "#c62828";
        return;
    }

    if (tshirtOrderQuantity() < 1 && kurtiOrderQuantity() < 1) {
        statusEl.textContent = "Please choose at least one size and quantity for a T-shirt or Kurti.";
        statusEl.style.color = "#c62828";
        return;
    }

    statusEl.textContent = "Submitting...";
    statusEl.style.color = "#888";

    try {
        const res = await fetch("/order-tshirt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Order failed.");
        }

        statusEl.textContent = "";

        if (typeof closeTshirtModal === "function") {
            closeTshirtModal();
        }

        if (typeof showThankYouPopup === "function") {
            showThankYouPopup(name, "reserving your T-shirt / Kurti");
        }

        document.getElementById("tshirt-order-form").reset();
        updateTshirtTotal();

    } catch (err) {
        statusEl.textContent = "❌ " + err.message;
        statusEl.style.color = "#c62828";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadTshirtPrice();
    [
        "tshirt-xs", "tshirt-small", "tshirt-medium", "tshirt-large", "tshirt-xl", "tshirt-xxl",
        "kurti-xs", "kurti-small", "kurti-medium", "kurti-large", "kurti-xl", "kurti-xxl"
    ].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("input", updateTshirtTotal);
    });
});


// ===== T-Shirt Order Modal open/close =====
function openTshirtModal() {
    const overlay = document.getElementById("tshirt-modal-overlay");
    if (!overlay) return;
    overlay.style.display = "flex";
    loadTshirtPrice();
}

function closeTshirtModal() {
    const overlay = document.getElementById("tshirt-modal-overlay");
    if (!overlay) return;
    overlay.style.display = "none";
}


// ===== T-Shirt Order: auto-fill for a returning resident =====
let tshirtLastLookedUpMobile = "";

async function lookupTshirtResident() {
    const mobileInput = document.getElementById("tshirt-mobile");
    if (!mobileInput) return;

    const mobile = mobileInput.value.trim();

    if (!/^\d{10}$/.test(mobile) || mobile === tshirtLastLookedUpMobile) {
        return;
    }

    tshirtLastLookedUpMobile = mobile;

    try {
        const res = await fetch("/api/lookup-resident/" + encodeURIComponent(mobile));
        const data = await res.json();

        if (data.found) {
            const nameEl = document.getElementById("tshirt-name");
            const blockEl = document.getElementById("tshirt-block");
            const flatEl = document.getElementById("tshirt-flat");

            if (nameEl && !nameEl.value) nameEl.value = data.name;
            if (blockEl && !blockEl.value) blockEl.value = data.block;
            if (flatEl && !flatEl.value) flatEl.value = data.flat_number;
        }
    } catch (err) {
        // Silent failure - this is a convenience, not a required step.
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const mobileEl = document.getElementById("tshirt-mobile");
    if (mobileEl) {
        mobileEl.addEventListener("input", lookupTshirtResident);
        mobileEl.addEventListener("blur", lookupTshirtResident);
    }
});


// ===== Copy UPI ID to clipboard (donation flow) =====
async function copyUpiId(buttonEl, upiId) {
    const originalText = buttonEl.textContent;

    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(upiId);
        } else {
            // Fallback for older/in-app browsers without Clipboard API
            const tempInput = document.createElement("textarea");
            tempInput.value = upiId;
            tempInput.style.position = "fixed";
            tempInput.style.opacity = "0";
            document.body.appendChild(tempInput);
            tempInput.focus();
            tempInput.select();
            document.execCommand("copy");
            document.body.removeChild(tempInput);
        }

        buttonEl.textContent = "✅ Copied!";
        buttonEl.style.background = "#c8e6c9";

    } catch (err) {
        buttonEl.textContent = "❌ Could not copy - select manually";
        buttonEl.style.background = "#ffcdd2";
    }

    setTimeout(() => {
        buttonEl.textContent = originalText;
        buttonEl.style.background = "#eee";
    }, 2500);
}
