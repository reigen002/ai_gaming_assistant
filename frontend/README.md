# 🎮 Frontend - Game Assistant Sidebar

A resizable, toggleable sidebar UI component for querying game-related information in real-time. Built with vanilla HTML5, CSS3, and JavaScript - no framework dependencies.

## ✨ Features

### UI Components
- **Windows-style Sidebar**: Fixed right-side panel, smooth animations
- **Toggle Button**: Top-right button or `Ctrl+K` to open/close
- **Resizable Panel**: Drag left edge to adjust width (280px - 600px range)
- **Dark Gaming Theme**: Gradient accents, shadow effects, minimal aesthetic
- **Responsive Design**: Adapts to mobile, tablet, desktop screens

### Form & Input
- **Game Name Field**: Text input for game title
- **Query Textarea**: Multi-line input for questions
- **Submit Button**: Sends query to backend
- **Real-time Status**: Shows Loading, Success, or Error states

### State Management
- **Conversation History**: Message list with user/assistant separation
- **LocalStorage Persistence**: Form state, sidebar position, conversations
- **Auto-save**: All data persists across sessions and page reloads

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `Cmd+K` | Toggle sidebar |
| `Escape` | Close sidebar |
| `Enter` (form) | Submit query |

## 📂 Project Structure

```
frontend/
├── index.html       # Main HTML with sidebar structure
├── styles.css       # CSS variables + styling
├── script.js        # JavaScript interactivity
└── README.md        # This file
```

## 🏗️ How It Works

### JavaScript Architecture
```
GameAssistantSidebar class
├── UI Management
│   ├── openSidebar()
│   ├── closeSidebar()
│   ├── toggleSidebar()
│   └── startResize()/resize()/stopResize()
│
├── Data Handling
│   ├── handleFormSubmit()
│   ├── submitQuery()
│   └── submitToBackend(gameName, query)
│
└── Persistence
    ├── saveState() → localStorage
    └── loadState() → restore on reload
```

### API Integration
**Endpoint**: `POST /chat`

**Request**:
```json
{
  "game_name": "Valorant",
  "message": "best agent for beginners?",
  "conversation_id": "uuid-optional"
}
```

**Response**:
```json
{
  "conversation_id": "uuid",
  "game_name": "Valorant",
  "answer": "Phoenix, Sage, and Brimstone...",
  "timestamp": "2026-05-02T12:34:56"
}
```

## 🚀 Getting Started

### Quick Start
1. **Start backend** (from project root)
   ```bash
   cd backend/rpgagents
   python main.py api
   ```

2. **Start frontend server**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

3. **Open browser**
   ```
   http://localhost:3000
   ```

4. **Use sidebar**
   - Sidebar opens by default
   - Enter game name
   - Type your question
   - Submit with button or Enter key

### Backend API URL
By default, frontend connects to `http://localhost:8000` (FastAPI backend).

To change, edit [script.js](script.js) line ~12:
```javascript
const apiBase = 'http://localhost:8000';  // Change here
```

## 🎨 Styling Customization

### CSS Variables
Edit `:root` in [styles.css](styles.css) to customize:

```css
:root {
    --primary-color: #3dd6a0;        /* Teal accent */
    --secondary-color: #16a3d9;      /* Blue accent */
    --bg-dark: #0a0f14;              /* Very dark background */
    --bg-panel: #0f1419;             /* Dark panel background */
    --bg-input: #151d27;             /* Input background */
    --text-light: #e0e0e0;           /* Light text */
    --border-color: #2a3a4a;         /* Subtle borders */
    --sidebar-width: 380px;          /* Default sidebar width */
    --sidebar-min-width: 280px;      /* Minimum width */
    --sidebar-max-width: 600px;      /* Maximum width */
}
```

### Dark Theme
The entire theme is dark by default - suitable for gaming overlays. Modify `.sidebar` and `.message-item` classes to change overall appearance.

## 📋 Testing Checklist

- [ ] **Sidebar Toggle**: Button and `Ctrl+K` work
- [ ] **Form Input**: Can type game name and query
- [ ] **Submit**: Button and Enter key both work
- [ ] **Message Display**: User/assistant messages appear in list
- [ ] **Resize**: Can drag left edge to resize (280px-600px)
- [ ] **Persistence**: Data saved on refresh
- [ ] **Keyboard**: `Escape` closes sidebar
- [ ] **Responsive**: Works on mobile/tablet
- [ ] **Status**: Loading/error states display
- [ ] **API**: Connected to backend (check network tab)

## 🔗 Integration with Backend

### API Configuration
The frontend is pre-configured to work with the FastAPI backend at `http://localhost:8000`.

**Key method**: `submitToBackend()` in [script.js](script.js#L110)
```javascript
async submitToBackend(gameName, query) {
  const response = await fetch(`${this.apiBase}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      game_name: gameName,
      message: query,
      conversation_id: this.currentConversationId
    })
  });
  return response.json();
}
```

### Testing Connection
1. Open browser DevTools (`F12`)
2. Go to Network tab
3. Submit a query
4. Should see POST to `http://localhost:8000/chat`
5. Response should have `answer`, `conversation_id`, etc.

## 🖥️ Embeddable in Game Overlays

### Steam Overlay Browser
The sidebar works in Steam's overlay browser:
1. Add to Steam as non-game shortcut pointing to `http://localhost:3000`
2. Launch and open with overlay (`Shift+Tab`)
3. Sidebar is already toggleable with `Ctrl+K`

### Overwolf App
To embed as Overwolf app:
1. Create `manifest.json` pointing to index.html
2. Sidebar will work as-is
3. Handle Overwolf API for window management

### OBS Browser Source
1. Add Browser Source pointing to `http://localhost:3000`
2. Set transparent background
3. Adjust resolution/position as needed

## 📱 Responsive Behavior

| Screen Size | Behavior |
|------------|----------|
| Desktop (> 768px) | Sidebar 280-600px, resizable |
| Tablet (≤ 768px) | Sidebar 280px fixed |
| Mobile (< 480px) | Sidebar 280px, full height |

Adjust media query in [styles.css](styles.css#L185) if needed.

## 🔧 Troubleshooting

### "Cannot connect to backend"
- Verify backend is running on port 8000
- Check browser console (F12) for CORS errors
- Ensure `.env` has API keys set in backend

### "Sidebar not showing messages"
- Clear localStorage: `localStorage.clear()` in console
- Check network tab for `/chat` requests
- Verify API response format in browser console

### "Sidebar not resizable"
- Check mouse events are not being blocked
- Verify CSS isn't overriding resize styles
- Ensure JavaScript is enabled

### "Keyboard shortcuts not working"
- Focus might be in textarea - press Escape first
- Check for conflicting browser shortcuts
- Verify JavaScript is enabled

## 📝 Code Structure

### Main Class: `GameAssistantSidebar`

**Constructor**:
```javascript
constructor(containerId, apiBase='http://localhost:8000')
```

**Key Methods**:
- `toggleSidebar()` - Toggle open/close
- `openSidebar()` / `closeSidebar()` - Explicit control
- `startResize()` / `resize()` / `stopResize()` - Width adjustment
- `handleFormSubmit()` - Form validation
- `submitToBackend()` - API call
- `addResultItem()` - Display message
- `saveState()` / `loadState()` - Persistence

## 🎯 Next Steps

1. **Connect to Backend**: Verify `http://localhost:8000` is set in script.js
2. **Test Queries**: Try different games and questions
3. **Customize Colors**: Edit CSS variables in `:root`
4. **Deploy**: Host on web server for production use

## ✍️ Notes

- No external dependencies (no jQuery, React, etc.)
- Pure vanilla JavaScript - easier to debug
- LocalStorage limits to ~5-10MB per domain
- For games with many conversations, consider upgrading to IndexedDB
- Sidebar defaults to **open** on first load
- All UI state is preserved in browser localStorage
- Simulated responses are currently used for demonstration
- Ready for real backend API integration via the `submitToBackend()` method
