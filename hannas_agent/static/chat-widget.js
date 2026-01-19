// Rotating system greetings
const GREETINGS = [
  "🌸 Hi! I’m Hanna's AI Care Concierge. How can I support you and your baby today?",
  "👶 Hello! Need tips on newborn care, meals, or postpartum recovery? I’m here to help!",
  "🍲 Hi there! I can guide you on baby care, meals, home support, or massage. What would you like?",
  "🌷 Welcome! I’m your postpartum support assistant. Ask me anything about caring for you and your newborn.",
  "🤱 Hi! Congratulations on your new arrival! How can I assist you today with baby care or postpartum needs?"
];

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("chat-toggle");
    const widget = document.getElementById("chat-widget");
    const closeBtn = document.getElementById("chat-close");
    const speechBubble = document.getElementById("speech-bubble");
    const sendBtn = document.getElementById("send-btn");
    const input = document.getElementById("user-input");
    const messages = document.getElementById("chat-messages");

    toggle.onclick = () => {
    widget.style.display = "flex";
    speechBubble.style.display = "none";
    // Lock body scroll on mobile to prevent displacement
    if (window.innerWidth <= 768) {
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
        document.body.style.height = '100%';
    }
    // Show rotating system greeting if there are no messages yet
    showInitialGreetingIfNeeded();
    input.focus();
    };
    closeBtn.onclick = () => {
    widget.style.display = "none";
    speechBubble.style.display = "block";
    // Unlock body scroll
    if (window.innerWidth <= 768) {
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
        document.body.style.height = '';
    }
    };
});

function showInitialGreetingIfNeeded() {
  // Only add greeting if there are no messages yet
  if (!messages || messages.children.length > 0) return;
  const raw = localStorage.getItem('hanna_greeting_index') || '0';
  let idx = parseInt(raw, 10);
  if (Number.isNaN(idx)) idx = 0;
  const greeting = GREETINGS[idx % GREETINGS.length];
  addMessage(greeting, 'assistant', false);
  // advance index for next user (rotate)
  localStorage.setItem('hanna_greeting_index', String((idx + 1) % GREETINGS.length));
}



function addMessage(text, sender, isMarkdown = false) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  
  if (sender === "assistant" && text === "Typing...") {
    // Show animated typing indicator
    div.className = "message assistant";
    div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  } else if (isMarkdown && sender === "assistant") {
    // Parse and render Markdown
    const formattedText = text.replace(/\\n/g, '\n');
    div.innerHTML = marked.parse(formattedText);
  } else {
    div.innerText = text;
  }
  
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  input.disabled = true;
  sendBtn.disabled = true;

  const typingMsg = addMessage("Typing...", "assistant");

  try {
      const res = await fetch("https://hannas-chat-agent-production.up.railway.app/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
          message: text,
          session_id: localStorage.getItem("chat_session") || null
          })
      });

      const data = await res.json();
      localStorage.setItem("chat_session", data.session_id);

    typingMsg.remove();
    // Render response as Markdown
    addMessage(data.response, "assistant", true);
  } catch (err) {
    typingMsg.remove();
      addMessage("Error: Could not get response.", "assistant");
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    // On mobile, blur the input to dismiss keyboard and restore full view
    if (window.innerWidth <= 768) {
      try {
        input.blur();
      } catch (e) {}
      // Give keyboard a moment to dismiss then reset app height
      setTimeout(() => {
        setAppHeight();
        messages.scrollTop = messages.scrollHeight;
      }, 150);
    } else {
      input.focus();
    }
  }
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !input.disabled) {
    e.preventDefault();
    sendMessage();
  }
});

// When input focuses on mobile, adjust viewport and ensure input is visible
input.addEventListener('focus', () => {
  if (window.innerWidth <= 768) {
    // wait for keyboard animation and then update visual viewport height
    setTimeout(() => {
      setAppHeight();
      messages.scrollTop = messages.scrollHeight; // Scroll to bottom
      try { input.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) {}
    }, 300);
  }
});

// Mobile keyboard fix: keep input visible when virtual keyboard opens
function setAppHeight() {
  if (window.visualViewport) {
    const vh = window.visualViewport.height;
    const offsetTop = window.visualViewport.offsetTop;
    document.documentElement.style.setProperty('--app-height', `${vh}px`);
    // Adjust widget position when keyboard pushes viewport
    if (widget.style.display === 'flex' && window.innerWidth <= 768) {
      widget.style.transform = `translateY(${offsetTop}px)`;
      // Always scroll to bottom when height changes
      setTimeout(() => {
        messages.scrollTop = messages.scrollHeight;
      }, 50);
    }
  } else {
    const vh = window.innerHeight;
    document.documentElement.style.setProperty('--app-height', `${vh}px`);
  }
}

setAppHeight();
window.addEventListener('resize', setAppHeight);
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', setAppHeight);
  window.visualViewport.addEventListener('scroll', setAppHeight);
}
