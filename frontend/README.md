# RPG Game Assistant - Frontend

A resizable, toggleable sidebar UI component for querying game-related information.

## Features

### Sidebar UI
- **Windows-style Sidebar**: Fixed right-side panel with smooth toggle behavior
- **Toggleable**: Open/close with button, keyboard shortcuts, or close button
- **Resizable**: Drag the left edge of the sidebar to adjust width (280px - 600px min/max)
- **Responsive**: Adapts to different screen sizes
- **Gaming Aesthetic**: Clean, minimal dark theme with gradient accents

### Form Components
- **Game Name Input**: Text field for specifying the game
- **Query Textarea**: Multi-line input for questions/queries
- **Submit Button**: Send query to backend (ready for API integration)

### Interactive Features
- **Status Display**: Real-time feedback (Ready, Loading, Success, Error)
- **Results Area**: Shows conversation history with scrollable area
- **Auto-save**: Form state and sidebar preferences saved to localStorage
- **Keyboard Shortcuts**:
  - `Ctrl+K` (or `Cmd+K` on Mac): Toggle sidebar open/close
  - `Escape`: Close sidebar

## Directory Structure

```
frontend/
├── index.html      # HTML structure with sidebar and form
├── styles.css      # Styling and responsive design
├── script.js       # JavaScript for interactivity and state management
└── README.md       # This file
```

## Component Breakdown

### HTML (index.html)
- Main content area placeholder
- Sidebar container with form inputs
- Toggle and close buttons
- Results/status display areas

### CSS (styles.css)
- CSS variables for theming (colors, spacing, transitions)
- Gaming aesthetic with gradients and shadows
- Smooth animations for open/close and resize
- Responsive design for mobile/tablet
- Custom scrollbar styling

### JavaScript (script.js)
- `GameAssistantSidebar` class managing all interactions
- Toggle, resize, and form submission logic
- LocalStorage integration for persistence
- Ready for backend API integration via the `submitToBackend()` method

## How to Test

### Option 1: Direct Browser (Recommended)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Open `index.html` directly in a browser:
   ```bash
   # macOS/Linux
   open index.html
   
   # Windows (PowerShell)
   Start-Process index.html
   ```

### Option 2: Simple HTTP Server
1. Start a local HTTP server:
   ```bash
   # Python 3
   python -m http.server 3000
   
   # Node.js
   npx http-server -p 3000
   ```

2. Open browser to: `http://localhost:3000`

## Testing Checklist

- [ ] Sidebar opens/closes with button click
- [ ] Keyboard shortcuts work (Ctrl+K, Escape)
- [ ] Sidebar width is resizable by dragging the left edge
- [ ] Form inputs can be filled and submitted
- [ ] Results appear in the conversation area
- [ ] Sidebar state persists on page refresh
- [ ] Responsive on mobile devices
- [ ] Close button hides sidebar
- [ ] Status messages update correctly
- [ ] Buttons disable during operations

## Backend Integration

The component is ready to connect to the FastAPI backend. To enable real API calls:

1. Start the backend API:
   ```bash
   cd backend/rpgagents
   python -m uvicorn src.rpgagents.api:app --host 0.0.0.0 --port 8000
   ```

2. In `script.js`, replace the `simulateResponse()` call in `handleFormSubmit()` with `submitToBackend()`:

   **Current** (lines ~130):
   ```javascript
   await this.simulateResponse(gameName, query);
   ```

   **Change to**:
   ```javascript
   const answer = await this.submitToBackend(gameName, query);
   this.addResultItem(answer, 'assistant');
   ```

3. This will send queries to `POST /chat` endpoint and display real responses.

## Styling Customization

Edit `:root` CSS variables in `styles.css` to customize colors and dimensions:

```css
:root {
    --primary-color: #3dd6a0;        /* Main accent color */
    --secondary-color: #16a3d9;      /* Secondary accent */
    --bg-dark: #0a0f14;              /* Dark background */
    --bg-panel: #0f1419;             /* Panel background */
    --sidebar-width: 380px;          /* Default sidebar width */
}
```

## Keyboard Shortcuts Reference

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `Cmd+K` | Toggle sidebar |
| `Escape` | Close sidebar |
| `Enter` (in form) | Submit query |

## Notes

- The sidebar defaults to **open** on first load (via CSS class `open`)
- Sidebar width is constrained between 280px and 600px
- All UI state is preserved in browser localStorage
- Simulated responses are currently used for demonstration
- Ready for real backend API integration via the `submitToBackend()` method
