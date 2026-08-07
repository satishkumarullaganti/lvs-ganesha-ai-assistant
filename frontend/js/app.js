const sendButton = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const chatContainer = document.getElementById("chat-container");
// ======================================
// Quick Registration Modal
// ======================================

const quickRegisterCard = document.getElementById("quick-register-card");

const registrationModal = document.getElementById("registration-modal");

const closeModal = document.getElementById("close-modal");

const registerSubmitBtn = document.getElementById("register-submit");

const competitionField = document.getElementById("competition");
const nameField = document.getElementById("reg-name");
const blockField = document.getElementById("reg-block");
const flatField = document.getElementById("reg-flat");
const mobileField = document.getElementById("reg-mobile");
const ageField = document.getElementById("reg-age");

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

    registrationModal.style.display = "block";

});

closeModal.addEventListener("click", function () {

    registrationModal.style.display = "none";

});

window.addEventListener("click", function (event) {

    if (event.target === registrationModal) {

        registrationModal.style.display = "none";

    }

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

    if (registrationData.age === "" || Number(registrationData.age) <= 0) {
        alert("Please enter a valid age.");
        ageField.focus();
        return;
    }

    registerSubmitBtn.disabled = true;
    registerSubmitBtn.innerHTML = "Registering...";

    try {

        const response = await fetch("http://127.0.0.1:8000/register", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(registrationData)

        });

        if (!response.ok) {
            throw new Error("Registration failed");
        }

        alert("✅ Registration successful for " + registrationData.name + "!");

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

        const response = await fetch("http://127.0.0.1:8000/chat", {

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
// Donation Payment Confirmation Button
// ======================================

function confirmDonationPaid() {

    userInput.value = "paid";

    sendMessage();

}