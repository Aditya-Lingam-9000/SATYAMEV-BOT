/* ==========================================================================
   SATYAMEV-BOT INTERACTIVITY AND CHAT SIMULATOR SCRIPT
   ========================================================================== */

// Tab switcher logic
function switchTab(tabName) {
  // Deactivate all tab buttons
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => btn.classList.remove('active'));

  // Hide all tab contents
  const contents = document.querySelectorAll('.tab-content');
  contents.forEach(content => content.classList.remove('active'));

  // Activate selected button and content
  event.currentTarget.classList.add('active');
  const targetContent = document.getElementById(`tab-${tabName}`);
  if (targetContent) {
    targetContent.classList.add('active');
  }

  // Restart chat simulation based on tab name
  playChatSimulation(tabName);
}

// Clipboard copy logic
function copyText(elementId) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const text = element.innerText || element.textContent;
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.currentTarget;
    const originalText = btn.innerText;
    btn.innerText = 'Copied!';
    btn.style.background = '#10b981'; // Green accent
    
    setTimeout(() => {
      btn.innerText = originalText;
      btn.style.background = '';
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy text: ', err);
  });
}

// Scroll animation trigger using Intersection Observer
document.addEventListener('DOMContentLoaded', () => {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  const animatedElements = document.querySelectorAll('.fade-in-element');
  animatedElements.forEach(el => observer.observe(el));

  // Initialize first chat simulation
  playChatSimulation('text');
});

// Chat Dialog Scenarios mapping
const chatScenarios = {
  text: [
    { type: 'sent', text: 'join sandbox-code' },
    { type: 'received', text: 'Twilio Sandbox Joined! Send your claim text, screenshot, or audio to start.' },
    { type: 'sent', text: 'Did NASA confirm an asteroid is hitting Earth tomorrow?' },
    { type: 'status', text: 'Processing claim', percent: 20 },
    { type: 'status', text: 'Searching web databases', percent: 60 },
    { type: 'status', text: 'Analyzing evidence', percent: 100 },
    { type: 'received', text: '━━━━━━━━━━━━━━━\n❌ *VERDICT: FALSE*\n━━━━━━━━━━━━━━━\n\n*CONFIDENCE:* 98%\n\n*ANALYSIS*\nNASA\'s Planetary Defense Coordination Office has confirmed that there are no asteroids on a collision course with Earth tomorrow. The viral post is entirely fabricated.\n\n*SUPPORTING EVIDENCE*\n• NASA\'s database lists all near-Earth object trajectories, confirming zero threats.\n• Leading astronomical observatories report no unusual orbital movements.\n\n*VERIFIED SOURCES*\n1. nasa.gov\nhttps://nasa.gov' }
  ],
  image: [
    { type: 'sent', text: '📷 [Sent News Image Screenshot]' },
    { type: 'status', text: 'Downloading media file', percent: 15 },
    { type: 'status', text: 'Extracting text content from claim', percent: 40 },
    { type: 'status', text: 'Searching trusted web databases', percent: 70 },
    { type: 'status', text: 'Analyzing evidence', percent: 100 },
    { type: 'received', text: '━━━━━━━━━━━━━━━\n⚠️ *VERDICT: MISLEADING*\n━━━━━━━━━━━━━━━\n\n*CONFIDENCE:* 88%\n\n*ANALYSIS*\nThe screenshot claims that the government is issuing free smartphones to all citizens next month. This is a recurring scam link designed to steal user credentials. The official department has debunked this scheme.\n\n*SUPPORTING EVIDENCE*\n• The Press Information Bureau (PIB) issued a warning classifying the portal as a phishing link.\n\n*VERIFIED SOURCES*\n1. pib.gov.in\nhttps://pib.gov.in' }
  ],
  audio: [
    { type: 'sent', text: '🎙️ [Sent Voice Note (Telugu)]' },
    { type: 'status', text: 'Downloading media file', percent: 15 },
    { type: 'status', text: 'Extracting text content from claim', percent: 45 },
    { type: 'status', text: 'Analyzing evidence and synthesizing verdict', percent: 80 },
    { type: 'status', text: 'Fact-check report compiled', percent: 100 },
    { type: 'received', text: '━━━━━━━━━━━━━━━\n✅ *తీర్పు: నిజం (TRUE)*\n━━━━━━━━━━━━━━━\n\n*విశ్వాసార్హత స్థాయి:* 92%\n\n*ವಿಶ್ಲೇಷಣೆ*\nఈ వైరల్ ఆడియోలో పేర్కొన్నట్లుగా, రిజర్వ్ బ్యాంక్ కొత్త సెక్యూరిటీ నిబంధనలను విడుదల చేసిన మాట వాస్తవం. కొత్త గైడ్‌లైన్స్ అధికారిక నోటిఫికేషన్ ద్వారా ధృవీకరించబడ్డాయి.\n\n*సహాయక సాక్ష్యాలు*\n• RBI అధికారిక వెబ్‌సైట్ జూన్ 15 తేదీతో ప్రెస్ రిలీజ్ విడుదల చేసింది.\n\n*ధృవీకరించబడిన మూలాలు*\n1. rbi.org.in\nhttps://rbi.org.in' }
  ]
};

let currentTimeoutIds = [];
let statusBubbleElement = null;

// Chat Simulation Player
function playChatSimulation(scenarioName) {
  const chatLog = document.getElementById('chat-log');
  const botStatus = document.getElementById('chat-bot-status');
  const inputField = document.getElementById('chat-input-field');
  
  if (!chatLog) return;
  
  // Clear any active timeouts and current elements
  currentTimeoutIds.forEach(id => clearTimeout(id));
  currentTimeoutIds = [];
  chatLog.innerHTML = '';
  statusBubbleElement = null;
  botStatus.innerText = 'online';
  inputField.value = '';

  const steps = chatScenarios[scenarioName];
  let delay = 300;

  steps.forEach((step, index) => {
    const timeoutId = setTimeout(() => {
      // Simulate Bot online/typing status
      if (step.type === 'received') {
        botStatus.innerText = 'typing...';
      }

      setTimeout(() => {
        botStatus.innerText = 'online';

        if (step.type === 'sent') {
          // Add user bubble
          addChatBubble(chatLog, step.text, 'sent');
          // Update placeholder input display to show the typed message
          inputField.value = step.text;
        } 
        else if (step.type === 'status') {
          // Dynamic text-only status progress animation (Strategy 2)
          updateProgressBubble(chatLog, step.text, step.percent);
        } 
        else if (step.type === 'received') {
          // If we had a progress bubble, let's remove it once final verdict is ready
          if (statusBubbleElement) {
            statusBubbleElement.remove();
            statusBubbleElement = null;
          }
          // Add final response bubble
          addChatBubble(chatLog, step.text.replace(/\n/g, '<br>'), 'received');
          inputField.value = '';
        }
        
        // Auto scroll to bottom
        chatLog.scrollTop = chatLog.scrollHeight;
      }, step.type === 'received' ? 800 : 0);

    }, delay);

    // Increment running timeline delay
    delay += step.type === 'status' ? 1200 : 1800;
  });
}

function addChatBubble(container, text, type) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble bubble-${type}`;
  bubble.innerHTML = text;
  container.appendChild(bubble);
}

function updateProgressBubble(container, statusText, percent) {
  // If progress bubble doesn't exist, create it
  if (!statusBubbleElement) {
    statusBubbleElement = document.createElement('div');
    statusBubbleElement.className = 'chat-bubble bubble-progress';
    container.appendChild(statusBubbleElement);
  }
  
  // Formulate progress bar layout
  const bars = Math.floor(percent / 10);
  const progressBar = '[' + '█'.repeat(bars) + '░'.repeat(10 - bars) + ']';
  
  statusBubbleElement.innerHTML = `${statusText}...<br>${progressBar} ${percent}%`;
}
