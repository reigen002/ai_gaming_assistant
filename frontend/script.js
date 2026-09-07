/**
 * RPG Game Assistant - Frontend Sidebar Component
 * Handles UI interactions: toggle, resize, form submission
 */

class GameAssistantSidebar {
    constructor() {
        this.sidebarContainer = document.getElementById('sidebarContainer');
        this.sidebar = document.getElementById('sidebar');
        this.toggleBtn = document.getElementById('toggleBtn');
        this.closeBtn = document.getElementById('closeBtn');
        this.resizeHandle = document.getElementById('resizeHandle');
        this.queryForm = document.getElementById('queryForm');
        this.gameNameInput = document.getElementById('gameName');
        this.queryInput = document.getElementById('queryInput');
        this.submitBtn = document.getElementById('submitBtn');
        this.statusText = document.getElementById('statusText');
        this.resultsList = document.getElementById('resultsList');
        this.mainContent = document.getElementById('mainContent');

        // API Configuration
        this.API_BASE = 'http://localhost:8000'; // Change this if backend runs on different port
        this.currentConversationId = null;

        this.isResizing = false;
        this.startX = 0;
        this.startWidth = 0;
        this.sidebarWidth = 380; // default width

        this.init();
    }

    init() {
        this.attachEventListeners();
        this.restoreState();
    }

    attachEventListeners() {
        // Toggle buttons
        this.toggleBtn.addEventListener('click', () => this.toggleSidebar());
        this.closeBtn.addEventListener('click', () => this.closeSidebar());

        // Form submission
        this.queryForm.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // Resize handle
        this.resizeHandle.addEventListener('mousedown', (e) => this.startResize(e));
        document.addEventListener('mousemove', (e) => this.resize(e));
        document.addEventListener('mouseup', () => this.stopResize());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+K or Cmd+K to toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggleSidebar();
            }
            // Escape to close sidebar
            if (e.key === 'Escape' && this.isOpen()) {
                this.closeSidebar();
            }
        });

        // Auto-save form inputs
        this.gameNameInput.addEventListener('change', () => this.saveState());
        this.queryInput.addEventListener('change', () => this.saveState());
    }

    // ============ Toggle & Visibility ============

    toggleSidebar() {
        if (this.isOpen()) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        this.sidebarContainer.classList.remove('closed');
        this.sidebarContainer.classList.add('open');
        this.mainContent.classList.add('sidebar-open');
        this.gameNameInput.focus();
        this.saveState();
    }

    closeSidebar() {
        this.sidebarContainer.classList.remove('open');
        this.sidebarContainer.classList.add('closed');
        this.mainContent.classList.remove('sidebar-open');
        this.saveState();
    }

    isOpen() {
        return this.sidebarContainer.classList.contains('open');
    }

    // ============ Resize Functionality ============

    startResize(e) {
        if (e.button !== 0) return; // Only left mouse button

        this.isResizing = true;
        this.startX = e.clientX;
        this.startWidth = this.sidebarWidth;
        this.resizeHandle.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }

    resize(e) {
        if (!this.isResizing) return;

        const deltaX = this.startX - e.clientX; // Negative when dragging left
        let newWidth = this.startWidth + deltaX;

        // Constrain width between min and max
        const minWidth = 280;
        const maxWidth = 600;
        newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));

        this.sidebarWidth = newWidth;
        this.sidebar.style.width = `${newWidth}px`;
        this.resizeHandle.style.right = `${newWidth - 2}px`;
        this.mainContent.style.marginRight = `${newWidth}px`;

        // Update CSS variable for responsive design
        document.documentElement.style.setProperty('--sidebar-width', `${newWidth}px`);
    }

    stopResize() {
        if (!this.isResizing) return;

        this.isResizing = false;
        this.resizeHandle.classList.remove('resizing');
        document.body.style.cursor = 'auto';
        document.body.style.userSelect = 'auto';
        this.saveState();
    }

    // ============ Form Handling ============

    handleFormSubmit(e) {
        e.preventDefault();

        const gameName = this.gameNameInput.value.trim();
        const query = this.queryInput.value.trim();

        // Validation
        if (!gameName) {
            this.setStatus('Please enter a game name', 'error');
            this.gameNameInput.focus();
            return;
        }

        if (!query) {
            this.setStatus('Please enter a query', 'error');
            this.queryInput.focus();
            return;
        }

        // Submit query
        this.submitQuery(gameName, query);
    }

    async submitQuery(gameName, query) {
        this.setStatus('Sending query...', 'loading');
        this.submitBtn.disabled = true;

        try {
            // Display user query
            this.addResultItem(query, 'user');

            // Send to backend API
            const answer = await this.submitToBackend(gameName, query);
            this.addResultItem(answer, 'assistant');

            // Clear inputs after successful submission
            this.queryInput.value = '';
            this.queryInput.focus();

            this.setStatus('Ready', 'success');
        } catch (error) {
            this.setStatus(`Error: ${error.message}`, 'error');
        } finally {
            this.submitBtn.disabled = false;
        }
    }

    // ============ UI Updates ============

    addResultItem(content, role) {
        const resultItem = document.createElement('div');
        resultItem.className = `result-item ${role}`;
        resultItem.textContent = content;
        this.resultsList.appendChild(resultItem);

        // Auto-scroll to latest result
        const resultsArea = document.getElementById('resultsArea');
        resultsArea.scrollTop = resultsArea.scrollHeight;
    }

    setStatus(message, type = 'info') {
        this.statusText.textContent = message;
        this.statusText.className = 'status-text';
        if (type !== 'info') {
            this.statusText.classList.add(type);
        }
    }

    // ============ State Management ============

    saveState() {
        const state = {
            isOpen: this.isOpen(),
            sidebarWidth: this.sidebarWidth,
            gameName: this.gameNameInput.value,
            query: this.queryInput.value,
            conversationId: this.currentConversationId
        };
        localStorage.setItem('gameAssistantState', JSON.stringify(state));
    }

    restoreState() {
        const saved = localStorage.getItem('gameAssistantState');
        if (!saved) return;

        try {
            const state = JSON.parse(saved);

            // Restore sidebar state
            if (state.isOpen) {
                this.openSidebar();
            } else {
                this.closeSidebar();
            }

            // Restore sidebar width
            if (state.sidebarWidth) {
                this.sidebarWidth = state.sidebarWidth;
                this.sidebar.style.width = `${state.sidebarWidth}px`;
                this.resizeHandle.style.right = `${state.sidebarWidth - 2}px`;
                this.mainContent.style.marginRight = `${state.sidebarWidth}px`;
                document.documentElement.style.setProperty('--sidebar-width', `${state.sidebarWidth}px`);
            }

            // Restore form inputs
            if (state.gameName) {
                this.gameNameInput.value = state.gameName;
            }
            if (state.query) {
                this.queryInput.value = state.query;
            }

            // Restore conversation ID
            if (state.conversationId) {
                this.currentConversationId = state.conversationId;
            }
        } catch (error) {
            console.error('Error restoring state:', error);
        }
    }

    // ============ API Integration ============

    /**
     * Submit query to FastAPI backend /chat endpoint
     */
    async submitToBackend(gameName, query) {
        try {
            const response = await fetch(`${this.API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_name: gameName,
                    message: query,
                    conversation_id: this.currentConversationId
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Backend error: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Store conversation ID for future queries
            if (data.conversation_id) {
                this.currentConversationId = data.conversation_id;
                this.saveState();
            }

            return data.answer;
        } catch (error) {
            console.error('Backend API error:', error);
            throw new Error(`Failed to connect to backend: ${error.message}`);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.gameAssistant = new GameAssistantSidebar();
});
