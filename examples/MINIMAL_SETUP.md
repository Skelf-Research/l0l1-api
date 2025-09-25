# Minimal l0l1-UI Integration

## Required Dependencies Only

```bash
# Only install what's absolutely necessary
npm install @iconify/vue         # For icons (if not already installed)
npm install sortablejs           # For drag & drop (lightweight alternative)
# That's it! No CodeMirror needed.
```

## Alternative: Zero Additional Dependencies

If you want **zero** additional dependencies, here's what you get out of the box:

### 1. Pure SkeletonUI + TailwindCSS Components

```vue
<template>
  <div class="card">
    <header class="card-header">
      <h3 class="h3">SQL Analysis</h3>
    </header>

    <!-- Simple textarea for SQL -->
    <div class="p-4">
      <textarea
        class="textarea font-mono"
        placeholder="SELECT * FROM users"
        v-model="query"
        rows="6"
      ></textarea>
    </div>

    <!-- SkeletonUI buttons -->
    <div class="card-footer">
      <button class="btn variant-filled-primary" @click="analyzeQuery">
        <iconify-icon icon="mdi:play"></iconify-icon>
        <span>Analyze SQL</span>
      </button>
    </div>

    <!-- Results using SkeletonUI alerts -->
    <div v-if="results" class="p-4 space-y-4">
      <div v-if="results.pii_detected" class="alert variant-filled-warning">
        <iconify-icon icon="mdi:alert" slot="icon"></iconify-icon>
        <span>PII detected in your query</span>
      </div>

      <div v-if="results.validation" class="alert" :class="results.validation.is_valid ? 'variant-filled-success' : 'variant-filled-error'">
        <iconify-icon :icon="results.validation.is_valid ? 'mdi:check' : 'mdi:alert'" slot="icon"></iconify-icon>
        <span>{{ results.validation.is_valid ? 'Query is valid' : 'Query has issues' }}</span>
      </div>

      <div v-if="results.explanation" class="card variant-soft">
        <div class="card-header">
          <h4 class="h4">Explanation</h4>
        </div>
        <div class="p-4">
          {{ results.explanation }}
        </div>
      </div>
    </div>
  </div>
</template>
```

### 2. Basic Composable (No external deps)

```javascript
// composables/useL0L1.js
import { ref } from 'vue'

export function useL0L1() {
  const isLoading = ref(false)
  const error = ref(null)

  const analyzeSQL = async (query, options = {}) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await fetch('/api/sql/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          ...options
        })
      })

      if (!response.ok) throw new Error('Analysis failed')

      return await response.json()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return { analyzeSQL, isLoading, error }
}
```

## Progressive Enhancement Options

### Level 1: Basic SQL Analysis (Zero deps)
- Simple textarea
- Basic validation/PII detection
- SkeletonUI alerts for results

### Level 2: Enhanced UX (Minimal deps)
```bash
npm install sortablejs  # For reorderable cells
```
- Drag & drop cells
- Multiple cells
- Better UX

### Level 3: Full Notebook Experience (Optional)
```bash
npm install @monaco-editor/vue  # Only if you want advanced editor
# OR
npm install prismjs  # For syntax highlighting only
```

## Why This Approach is Better

### ✅ **Lighter Bundle**
- No CodeMirror (~200KB)
- No heavy dependencies
- Faster load times

### ✅ **Better SkeletonUI Integration**
- Uses your existing design system
- Consistent theming
- Native component behavior

### ✅ **Easier Maintenance**
- Fewer dependencies to update
- Less complexity
- Better TypeScript support

### ✅ **Mobile Friendly**
- Native textarea behavior
- Better touch interactions
- Responsive by default

## Implementation Strategy

### Phase 1: Start Simple
```vue
<!-- Just drop this into any page -->
<div class="card">
  <div class="p-4">
    <textarea class="textarea font-mono" v-model="sql" placeholder="SELECT * FROM users"></textarea>
    <button class="btn variant-filled-primary mt-4" @click="analyze">Analyze</button>
  </div>

  <div v-if="results" class="p-4">
    <div class="alert variant-filled-success" v-if="results.is_valid">
      Query is valid ✅
    </div>
    <div class="alert variant-filled-warning" v-if="results.pii_detected">
      PII detected ⚠️
    </div>
  </div>
</div>
```

### Phase 2: Add Notebook Features
- Multiple cells
- Save/load
- Export functionality

### Phase 3: Advanced Editor (Optional)
- Only add if users specifically request syntax highlighting
- Can be added later without breaking changes

## Zero-Dependency Example

Here's a complete working example with **no additional npm installs**:

```vue
<template>
  <div class="container mx-auto p-8">
    <div class="card">
      <header class="card-header">
        <h2 class="h2">SQL Analyzer</h2>
      </header>

      <div class="p-6">
        <!-- SQL Input -->
        <label class="label mb-4">
          <span>SQL Query</span>
          <textarea
            class="textarea font-mono mt-2"
            rows="8"
            placeholder="SELECT users.name, COUNT(orders.id) as order_count&#10;FROM users&#10;LEFT JOIN orders ON users.id = orders.user_id&#10;GROUP BY users.id"
            v-model="sqlQuery"
          ></textarea>
        </label>

        <!-- Options -->
        <div class="flex flex-wrap gap-4 mb-6">
          <label class="flex items-center space-x-2">
            <input class="checkbox" type="checkbox" v-model="validate" />
            <span>Validate</span>
          </label>
          <label class="flex items-center space-x-2">
            <input class="checkbox" type="checkbox" v-model="explain" />
            <span>Explain</span>
          </label>
          <label class="flex items-center space-x-2">
            <input class="checkbox" type="checkbox" v-model="checkPii" />
            <span>Check PII</span>
          </label>
        </div>

        <!-- Action Button -->
        <button
          class="btn variant-filled-primary"
          @click="analyzeQuery"
          :disabled="isAnalyzing || !sqlQuery.trim()"
        >
          <iconify-icon v-if="isAnalyzing" icon="mdi:loading" class="animate-spin"></iconify-icon>
          <iconify-icon v-else icon="mdi:play"></iconify-icon>
          <span>{{ isAnalyzing ? 'Analyzing...' : 'Analyze SQL' }}</span>
        </button>
      </div>

      <!-- Results -->
      <div v-if="analysisResults" class="border-t border-surface-300-600-token">
        <!-- PII Alert -->
        <div v-if="analysisResults.pii_detected?.length" class="m-6">
          <div class="alert variant-filled-warning">
            <iconify-icon icon="mdi:shield-alert" slot="icon"></iconify-icon>
            <span><strong>PII Detected:</strong> Found {{ analysisResults.pii_detected.length }} potential privacy issues</span>
          </div>
        </div>

        <!-- Validation Results -->
        <div v-if="analysisResults.validation" class="m-6">
          <div class="alert" :class="analysisResults.validation.is_valid ? 'variant-filled-success' : 'variant-filled-error'">
            <iconify-icon :icon="analysisResults.validation.is_valid ? 'mdi:check-circle' : 'mdi:alert-circle'" slot="icon"></iconify-icon>
            <span>{{ analysisResults.validation.is_valid ? 'Query is valid' : 'Query has validation issues' }}</span>
          </div>

          <div v-if="!analysisResults.validation.is_valid && analysisResults.validation.issues?.length" class="mt-4">
            <h4 class="h4 mb-2">Issues:</h4>
            <ul class="list-disc list-inside space-y-1 text-sm">
              <li v-for="issue in analysisResults.validation.issues" :key="issue" class="text-error-600-300-token">
                {{ issue }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Explanation -->
        <div v-if="analysisResults.explanation" class="m-6">
          <div class="card variant-soft">
            <header class="card-header">
              <h4 class="h4 flex items-center">
                <iconify-icon icon="mdi:lightbulb" class="mr-2"></iconify-icon>
                Query Explanation
              </h4>
            </header>
            <div class="p-4">
              <p class="leading-relaxed">{{ analysisResults.explanation }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const sqlQuery = ref('')
const validate = ref(true)
const explain = ref(true)
const checkPii = ref(true)
const isAnalyzing = ref(false)
const analysisResults = ref(null)

const analyzeQuery = async () => {
  if (!sqlQuery.value.trim() || isAnalyzing.value) return

  isAnalyzing.value = true
  analysisResults.value = null

  try {
    const results = {}

    // Validate if requested
    if (validate.value) {
      const response = await fetch('/api/sql/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: sqlQuery.value })
      })
      results.validation = await response.json()
    }

    // Check PII if requested
    if (checkPii.value) {
      const response = await fetch('/api/sql/check-pii', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: sqlQuery.value })
      })
      const piiResults = await response.json()
      results.pii_detected = piiResults.entities
    }

    // Explain if requested
    if (explain.value) {
      const response = await fetch('/api/sql/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: sqlQuery.value })
      })
      const explainResults = await response.json()
      results.explanation = explainResults.explanation
    }

    analysisResults.value = results

  } catch (error) {
    console.error('Analysis failed:', error)
    // Handle error with SkeletonUI toast
  } finally {
    isAnalyzing.value = false
  }
}
</script>
```

This gives you a **fully functional SQL analyzer** with zero additional dependencies beyond what you already have with SkeletonUI!