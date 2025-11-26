# l0l1 Frontend

Vue 3 + Tailwind CSS frontend for the l0l1 SQL Analysis Platform.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next-generation build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Pinia** - Vue store library
- **Vue Router** - Official router for Vue.js
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# From the frontend directory
npm install

# Or from root
make frontend-install
```

### Development

```bash
# Start development server (http://localhost:3000)
npm run dev

# Or from root
make frontend-dev
```

The development server proxies API requests to `http://localhost:8000`, so make sure the backend API is running:

```bash
# In another terminal, from root
make serve
```

### Production Build

```bash
npm run build
npm run preview  # Preview the build
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── assets/          # CSS and static files
│   │   └── main.css     # Tailwind + custom styles
│   ├── components/
│   │   ├── layout/      # Layout components (Sidebar, Header)
│   │   ├── common/      # Reusable UI components
│   │   └── sql/         # SQL-specific components
│   ├── composables/     # Vue composables
│   │   └── useApi.js    # API client and endpoints
│   ├── stores/          # Pinia stores
│   │   └── api.js       # API state management
│   ├── views/           # Page components
│   │   ├── DashboardView.vue
│   │   ├── WorkbenchView.vue
│   │   ├── WorkspacesView.vue
│   │   ├── LearningView.vue
│   │   └── SettingsView.vue
│   ├── router/          # Vue Router config
│   ├── App.vue          # Root component
│   └── main.js          # Application entry
├── index.html
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json
```

## Features

### Dashboard
- API health status
- Platform statistics
- Quick start guide

### SQL Workbench
- SQL query editor
- Multiple analysis modes:
  - **Validate** - Check SQL syntax and semantics
  - **Explain** - Get natural language explanations
  - **Complete** - AI-powered query completion
  - **Correct** - Fix broken SQL queries
  - **PII Check** - Detect personally identifiable information
- Sample queries for quick testing

### Workspaces
- Create and manage workspaces
- Set active workspace for API requests
- Schema management

### Learning Stats
- View learned query patterns
- Statistics on continuous learning
- Understanding how learning improves suggestions

### Settings
- API configuration
- Editor preferences
- Feature status

## API Integration

The frontend communicates with the l0l1 API through the proxy configured in `vite.config.js`. All API requests are prefixed with `/api` and proxied to the backend.

Key API endpoints used:
- `GET /health` - API health check
- `POST /sql/validate` - Validate SQL
- `POST /sql/explain` - Explain SQL
- `POST /sql/complete` - Complete SQL
- `POST /sql/correct` - Correct SQL
- `POST /sql/check-pii` - Check for PII
- `GET /workspaces` - List workspaces
- `POST /workspaces` - Create workspace
- `GET /learning/stats` - Get learning statistics

## Customization

### Theme
The color scheme is defined in `tailwind.config.js`. Modify the `primary` and `dark` color palettes to customize the look.

### Adding New Pages
1. Create a new view in `src/views/`
2. Add route in `src/router/index.js`
3. Add navigation item in `src/components/layout/Sidebar.vue`
