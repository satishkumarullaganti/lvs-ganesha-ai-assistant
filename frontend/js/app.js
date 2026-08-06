console.log("App.js loaded");

window.addEventListener("beforeunload", () => {
    console.log("PAGE IS RELOADING");
});
const sendButton = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const chatContainer = document.getElementById("chat-container");

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
