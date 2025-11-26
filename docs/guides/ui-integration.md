# l0l1 UI Integration Guide

This guide explains how to integrate l0l1's Jupyter-like functionality into your l0l1-ui (SkeletonUI + TailwindCSS + Vue.js) frontend.

## Architecture Overview

```
┌─────────────────┬─────────────────────────────────────┐
│   l0l1-ui       │           l0l1-api                  │
│   (Frontend)    │           (Backend)                 │
├─────────────────┼─────────────────────────────────────┤
│ • Vue.js        │ • FastAPI                           │
│ • SkeletonUI    │ • Jupyter Router (/jupyter/*)       │
│ • TailwindCSS   │ • UI Router (/ui/*)                 │
│ • NotebookUI    │ • Session Management                │
│                 │ • SQL Analysis                      │
│                 │ • PII Detection                     │
│                 │ • Learning Service                  │
└─────────────────┴─────────────────────────────────────┘
```

## Key Components

### 1. Backend API Endpoints

#### Jupyter-like Cell Execution
- `POST /jupyter/execute-cell` - Execute SQL cells with rich output
- `GET /jupyter/kernel-info` - Get kernel capabilities

#### UI Session Management
- `POST /ui/sessions` - Create new notebook sessions
- `GET /ui/sessions/{id}` - Get session details
- `POST /ui/sessions/{id}/cells` - Add cells to session
- `POST /ui/sessions/{id}/cells/{cell_id}/execute` - Execute specific cell

#### Rendering Helpers
- `POST /ui/render` - Render analysis results in Vue/Skeleton format

### 2. Frontend Vue Components

#### Core Components
- **NotebookInterface.vue** - Main notebook container
- **SQLCell.vue** - Interactive SQL cell with editor
- **SQLCellOutput.vue** - Rich output renderer
- **SQLAnalysisResults.vue** - Analysis results display

#### Composables
- **useNotebook.js** - API interaction layer

## Integration Steps

### Step 1: Install Dependencies

```bash
# In your l0l1-ui project
npm install codemirror vue-codemirror vuedraggable
npm install @skeletonlabs/skeleton # If not already installed
```

### Step 2: Copy Components

Copy the Vue components from `examples/vue_components/` to your project:

```bash
# Copy to your components directory
cp examples/vue_components/*.vue src/components/notebook/
cp examples/vue_components/composables/useNotebook.js src/composables/
```

### Step 3: Configure API Base URL

Update the `API_BASE` constant in `useNotebook.js`:

```javascript
const API_BASE = process.env.VUE_APP_API_URL || 'http://localhost:8000'
```

### Step 4: Add to Your Routes

```javascript
// router/index.js
const routes = [
  // ... your existing routes
  {
    path: '/notebook/:workspaceId?',
    name: 'Notebook',
    component: () => import('@/views/NotebookView.vue'),
    props: true
  }
]
```

### Step 5: Create Notebook View

```vue
<!-- views/NotebookView.vue -->
<template>
  <div class="notebook-view h-screen">
    <NotebookInterface
      :workspace-id="workspaceId || 'default'"
      :tenant-id="tenantId || 'default'"
      :notebook-title="notebookTitle"
      @session-created="onSessionCreated"
      @notebook-saved="onNotebookSaved"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NotebookInterface from '@/components/notebook/NotebookInterface.vue'

const props = defineProps({
  workspaceId: String
})

const tenantId = ref('default') // Get from user session
const notebookTitle = ref('SQL Analysis Notebook')

const onSessionCreated = (sessionId) => {
  console.log('Session created:', sessionId)
  // Store session ID for persistence
}

const onNotebookSaved = (data) => {
  console.log('Notebook saved:', data)
  // Handle notebook saving
}
</script>
```

## Advanced Integration Features

### 1. SkeletonUI Theme Integration

The components are designed to work with SkeletonUI themes:

```css
/* In your global CSS */
.sql-cell {
  @apply variant-ghost-surface;
}

.pii-warning {
  @apply variant-filled-warning;
}

.validation-error {
  @apply variant-filled-error;
}

.explanation-card {
  @apply variant-ghost-primary;
}
```

### 2. Workspace Integration

Connect notebooks to your existing workspace system:

```javascript
// In your workspace store/composable
import { useNotebook } from '@/composables/useNotebook'

export function useWorkspaceNotebooks(workspaceId) {
  const { listSessions, createSession } = useNotebook()

  const getNotebooks = async () => {
    return await listSessions({ workspace_id: workspaceId })
  }

  const createNotebook = async (title) => {
    return await createSession({
      workspace_id: workspaceId,
      metadata: { title }
    })
  }

  return { getNotebooks, createNotebook }
}
```

### 3. Schema Context Integration

Automatically load schema from your workspace:

```javascript
// In NotebookInterface.vue
import { useWorkspaceSchema } from '@/composables/useWorkspaceSchema'

const { getWorkspaceSchema } = useWorkspaceSchema()

onMounted(async () => {
  const schema = await getWorkspaceSchema(props.workspaceId)
  if (schema) {
    await updateSession(sessionId.value, {
      schema_context: schema.ddl
    })
  }
})
```

### 4. Real-time Collaboration

Add WebSocket support for real-time collaboration:

```javascript
// In NotebookInterface.vue
import { useWebSocket } from '@/composables/useWebSocket'

const { socket } = useWebSocket(`/ws/notebook/${sessionId.value}`)

socket.on('cell_executed', (data) => {
  // Update cell outputs in real-time
  onCellExecuted(data)
})

socket.on('cell_updated', (data) => {
  // Sync cell changes from other users
  syncCellUpdate(data)
})
```

## Styling and Theming

### TailwindCSS Classes

The components use semantic TailwindCSS classes that work well with SkeletonUI:

```css
/* Query display */
.query-display {
  @apply bg-surface-50 dark:bg-surface-800 rounded-lg p-4;
}

/* PII warning */
.pii-warning {
  @apply bg-warning-50 border-warning-200 text-warning-800;
  @apply dark:bg-warning-900/20 dark:border-warning-800 dark:text-warning-200;
}

/* Validation results */
.validation-success {
  @apply bg-success-50 border-success-200 text-success-800;
  @apply dark:bg-success-900/20 dark:border-success-800 dark:text-success-200;
}

.validation-error {
  @apply bg-error-50 border-error-200 text-error-800;
  @apply dark:bg-error-900/20 dark:border-error-800 dark:text-error-200;
}
```

### SkeletonUI Component Integration

Use SkeletonUI components within the notebook:

```vue
<!-- Using SkeletonUI Alert component -->
<Alert variant="warning" v-if="piiDetected">
  <svelte:fragment slot="icon">
    <Icon name="exclamation-triangle" />
  </svelte:fragment>
  <svelte:fragment slot="message">
    PII detected in your query
  </svelte:fragment>
</Alert>

<!-- Using SkeletonUI CodeBlock component -->
<CodeBlock
  language="sql"
  :code="queryContent"
  class="mb-4"
/>
```

## Performance Optimizations

### 1. Virtual Scrolling for Large Notebooks

```vue
<!-- For notebooks with many cells -->
<RecycleScroller
  class="scroller"
  :items="cells"
  :item-size="estimatedCellHeight"
  key-field="id"
  v-slot="{ item }"
>
  <SQLCell :cell="item" />
</RecycleScroller>
```

### 2. Debounced Auto-save

```javascript
import { debounce } from 'lodash-es'

const debouncedSave = debounce(async () => {
  await saveNotebook()
}, 2000)

watch(cells, debouncedSave, { deep: true })
```

### 3. Code Splitting

```javascript
// Lazy load heavy components
const SQLCell = defineAsyncComponent(() =>
  import('@/components/notebook/SQLCell.vue')
)
```

## Testing

### Unit Tests

```javascript
// tests/components/SQLCell.spec.js
import { mount } from '@vue/test-utils'
import SQLCell from '@/components/notebook/SQLCell.vue'

describe('SQLCell', () => {
  test('executes SQL query', async () => {
    const wrapper = mount(SQLCell, {
      props: {
        cellId: 'test-cell',
        sessionId: 'test-session'
      }
    })

    await wrapper.find('.execute-button').trigger('click')
    expect(wrapper.emitted('execute')).toBeTruthy()
  })
})
```

### Integration Tests

```javascript
// tests/integration/notebook.spec.js
import { render, screen } from '@testing-library/vue'
import NotebookInterface from '@/components/notebook/NotebookInterface.vue'

test('creates and executes SQL cells', async () => {
  render(NotebookInterface, {
    props: { workspaceId: 'test-workspace' }
  })

  // Test adding cells, executing queries, etc.
})
```

## Deployment Considerations

### 1. Environment Variables

```env
# Frontend (.env)
VUE_APP_API_URL=https://api.yourdomain.com
VUE_APP_WS_URL=wss://api.yourdomain.com/ws

# Backend
L0L1_API_HOST=0.0.0.0
L0L1_API_PORT=8000
OPENAI_API_KEY=your_key
```

### 2. Docker Integration

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### 3. Reverse Proxy Configuration

```nginx
# nginx.conf
location /api/ {
    proxy_pass http://l0l1-api:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location /ws/ {
    proxy_pass http://l0l1-api:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Conclusion

This integration provides a complete Jupyter-like experience within your Vue.js application, offering:

- ✅ Rich SQL analysis and validation
- ✅ Interactive code cells with syntax highlighting
- ✅ Real-time PII detection and anonymization
- ✅ AI-powered query completion and explanation
- ✅ Continuous learning from successful queries
- ✅ Session management and persistence
- ✅ Export/import functionality
- ✅ Responsive design with SkeletonUI components

The modular architecture allows you to integrate individual features gradually or use the complete notebook interface as a standalone feature in your application.