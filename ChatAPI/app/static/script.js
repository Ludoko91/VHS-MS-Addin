document.getElementById("send-button").addEventListener("click", () => {
    const input = document.getElementById("chat-input");
    const message = input.value;
    input.value = ""; // Eingabefeld leeren

    if (message.trim() === "") return;

    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML += `<div class="user-message">${message}</div>`;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_message: message })
    })
    .then(response => response.json())
    .then(data => {
        const answer = data.answer || "Fehler beim Abrufen der Antwort.";
        chatBox.innerHTML += `<div class="bot-message">${answer}</div>`;
    })
    .catch(error => {
        chatBox.innerHTML += `<div class="error-message">Fehler: ${error.message}</div>`;
    });
});
