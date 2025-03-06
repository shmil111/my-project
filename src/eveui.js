class EveUI {
    constructor() {
        this.initializeUI();
        this.setupEventListeners();
    }

    initializeUI() {
        // Initialize tabs
        this.tabs = document.querySelectorAll('.eve-nav-item');
        this.tabContents = document.querySelectorAll('.eve-tab-content');
        
        // Initialize scroll top button
        this.scrollTopBtn = document.querySelector('.eve-scroll-top');
        
        // Initialize message container
        this.messageContainer = document.getElementById('message-container');
        
        // Initialize status indicators
        this.apiStatus = document.getElementById('api-status');
    }

    setupEventListeners() {
        // Tab switching
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });

        // Scroll top button
        if (this.scrollTopBtn) {
            window.addEventListener('scroll', () => {
                this.scrollTopBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
            });

            this.scrollTopBtn.addEventListener('click', (e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        // Check API status
        this.checkApiStatus();
    }

    switchTab(tabId) {
        // Update active tab
        this.tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabId);
        });

        // Show corresponding content
        this.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === tabId);
        });

        // Scroll to tab content
        const targetContent = document.getElementById(tabId);
        if (targetContent) {
            targetContent.scrollIntoView({ behavior: 'smooth' });
        }
    }

    async checkApiStatus() {
        if (!this.apiStatus) return;

        try {
            const api = new EveApiClient();
            const response = await api.checkHealth();
            
            this.apiStatus.className = 'eve-status eve-status-online eve-mt-3';
            this.apiStatus.textContent = 'API is online';
        } catch (error) {
            this.apiStatus.className = 'eve-status eve-status-offline eve-mt-3';
            this.apiStatus.textContent = 'API is offline';
        }
    }

    // Animation utilities
    static animate(element, animation, duration = 300) {
        element.classList.add(animation);
        setTimeout(() => {
            element.classList.remove(animation);
        }, duration);
    }

    // Message handling
    addMessage(content, isUser = false) {
        if (!this.messageContainer) return;

        const messageEl = document.createElement('div');
        messageEl.className = `eve-message eve-message-${isUser ? 'user' : 'eve'}`;
        messageEl.innerHTML = `
            <div class="eve-message-content">${content}</div>
            <div class="eve-message-time">Just now</div>
        `;

        this.messageContainer.appendChild(messageEl);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.eveUI = new EveUI();
}); 