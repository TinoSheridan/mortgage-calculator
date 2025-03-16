// chat.js - Chat log functionality for mortgage calculator
document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.getElementById('chatToggle');
    const chatPanel = document.getElementById('chatPanel');
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const closeChat = document.getElementById('closeChat');
    
    // Chat session ID (using timestamp for simplicity)
    const sessionId = Date.now().toString();
    let chatVisible = false;
    
    // Initialize with user information or allow anonymous
    let userName = localStorage.getItem('chat_username') || '';
    if (!userName) {
        userName = 'User' + Math.floor(Math.random() * 10000);
        localStorage.setItem('chat_username', userName);
    }
    
    // Toggle chat panel visibility
    if (chatToggle) {
        chatToggle.addEventListener('click', function() {
            chatVisible = !chatVisible;
            chatPanel.style.display = chatVisible ? 'block' : 'none';
            
            if (chatVisible) {
                // Load chat history when opened
                loadChatHistory();
                messageInput.focus();
            }
        });
    }
    
    // Close chat button
    if (closeChat) {
        closeChat.addEventListener('click', function() {
            chatVisible = false;
            chatPanel.style.display = 'none';
        });
    }
    
    // Handle form submission
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message) {
                sendMessage(message);
                messageInput.value = '';
            }
        });
    }
    
    // Load chat history from server
    function loadChatHistory() {
        fetch('/api/chat/history?session=' + sessionId)
            .then(response => response.json())
            .then(data => {
                chatMessages.innerHTML = '';
                data.messages.forEach(message => {
                    appendMessage(message.user, message.text, message.timestamp);
                });
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                appendSystemMessage('Could not load chat history. Please try again later.');
            });
    }
    
    // Send message to server
    function sendMessage(text) {
        // Optimistically render message
        const timestamp = new Date().toISOString();
        appendMessage(userName, text, timestamp, 'user-message');
        scrollToBottom();
        
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // Send to server
        fetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                session_id: sessionId,
                user: userName,
                message: text,
                timestamp: timestamp
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                // If we get an automated response
                appendMessage('Support', data.response, new Date().toISOString(), 'system-message');
                scrollToBottom();
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            appendSystemMessage('Message could not be sent. Please try again.');
        });
    }
    
    // Append message to chat
    function appendMessage(user, text, timestamp, className = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${className}`;
        
        const time = new Date(timestamp);
        const timeString = time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="chat-header">
                <strong>${user}</strong>
                <span class="chat-time">${timeString}</span>
            </div>
            <div class="chat-text">${text}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
    }
    
    // Append system message
    function appendSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message system-message';
        messageDiv.innerHTML = `<div class="chat-text">${text}</div>`;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Poll for new messages every 10 seconds if chat is open
    let pollInterval;
    
    function startPolling() {
        pollInterval = setInterval(() => {
            if (chatVisible) {
                fetch('/api/chat/updates?session=' + sessionId + '&last=' + getLastMessageTime())
                    .then(response => response.json())
                    .then(data => {
                        if (data.messages && data.messages.length > 0) {
                            data.messages.forEach(message => {
                                appendMessage(message.user, message.text, message.timestamp);
                            });
                            scrollToBottom();
                        }
                    })
                    .catch(error => {
                        console.error('Error polling for updates:', error);
                    });
            }
        }, 10000);
    }
    
    function getLastMessageTime() {
        const messages = chatMessages.querySelectorAll('.chat-message');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const timeElement = lastMessage.querySelector('.chat-time');
            if (timeElement) {
                return timeElement.getAttribute('data-timestamp') || '';
            }
        }
        return '';
    }
    
    // Start polling for updates
    startPolling();
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        clearInterval(pollInterval);
    });
});
