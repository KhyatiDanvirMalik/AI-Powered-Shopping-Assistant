// static/script.js
(function () {
  document.addEventListener("DOMContentLoaded", () => {
    // Try to find existing elements by common IDs first, then by safe fallbacks.
    const form =
      document.getElementById("chat-form") ||
      document.querySelector("form");

    const input =
      document.getElementById("user-input") ||
      document.querySelector('input[type="text"], input[type="search"], textarea');

    const sendBtn =
      document.getElementById("send-btn") ||
      document.querySelector('button[type="submit"], button');

    // Message container (whatever your old UI uses)
    const chatBox =
      document.getElementById("chat-box") ||
      document.querySelector(".chat-box, .messages, .chat-window, .chat, .conversation");

    if (!form || !input || !sendBtn) {
      console.error("Chat elements not found. Ensure your page has a form, an input, and a button.");
      return;
    }

    // Helper: render a bubble (keeps your existing styles if classes exist)
    function addMessage(text, who) {
      // If you already had message markup/classes, this will reuse them.
      const bubble = document.createElement("div");
      bubble.className = `msg ${who}`; // your CSS can style .msg.user / .msg.ai (or ignore)
      bubble.textContent = text;

      if (chatBox) {
        chatBox.appendChild(bubble);
        chatBox.scrollTop = chatBox.scrollHeight;
      } else {
        // Fallback: if no chat container in old UI, append just above the form.
        form.parentNode.insertBefore(bubble, form);
      }
    }

    async function sendMessage(message) {
      if (!message) return;

      addMessage(message, "user");
      input.value = "";
      input.focus();

      const prevDisabled = sendBtn.disabled;
      sendBtn.disabled = true;

      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });

        let data;
        try {
          data = await res.json();
        } catch {
          data = { response: "Server returned no JSON." };
        }

        addMessage(data.response || "No response.", "ai");
      } catch (err) {
        console.error(err);
        addMessage("Network error while contacting the server.", "ai");
      } finally {
        sendBtn.disabled = prevDisabled;
      }
    }

    // Submit via form (Enter key)
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const msg = (input.value || "").trim();
      if (!msg) return;
      sendMessage(msg);
    });

    // Also handle explicit button clicks (in case button isn't type="submit")
    sendBtn.addEventListener("click", (e) => {
      // If it's already submit, the form handler will run; this is just a safety net.
      if (sendBtn.getAttribute("type") !== "submit") {
        e.preventDefault();
        const msg = (input.value || "").trim();
        if (!msg) return;
        sendMessage(msg);
      }
    });
  });
})();
