# l0l1 Analytics Workbench Integration Guide

This guide shows how to integrate the l0l1 SQL Analytics Workbench into your analyst dashboard - a souped-up SQL workbench interface for power users.

## 🎯 Design Philosophy

**Think DataGrip meets Jupyter meets modern web analytics**
- Professional 3-panel layout (schema browser, editor, results)
- Real-time AI analysis and suggestions
- Advanced query management and history
- Performance insights and optimization hints
- Seamless integration with your existing workspace system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Analytics Workbench                         │
├─────────────┬───────────────────────────┬─────────────────────┤
│   Schema    │      Query Editor         │    Query Info       │
│   Browser   │                           │                     │
│             │  ┌─────────────────────┐  │  • Learning Stats   │
│ • Tables    │  │                     │  │  • Recent Queries   │
│ • Views     │  │   SQL Editor        │  │  • Bookmarks        │
│ • Columns   │  │   with AI           │  │  • Performance      │
│ • Indexes   │  │   Assistant         │  │                     │
│             │  └─────────────────────┘  │                     │
│             │                           │                     │
│             │  ┌─────────────────────┐  │                     │
│             │  │                     │  │                     │
│             │  │   Analysis &        │  │                     │
│             │  │   Results Panel     │  │                     │
│             │  │                     │  │                     │
│             │  └─────────────────────┘  │                     │
└─────────────┴───────────────────────────┴─────────────────────┘
```

## 🚀 Key Features

### **1. Professional SQL Editor**
- **Line numbers and cursor position tracking**
- **SQL syntax awareness** (auto-format, templates)
- **Keyboard shortcuts** (F5 to run, Ctrl+Enter, etc.)
- **Query templates** (SELECT, JOIN, GROUP BY, Window functions)

### **2. Live AI Assistant**
- **Real-time PII detection** as you type
- **Query suggestions** based on learning data
- **Performance optimization** hints
- **Auto-completion** from schema and history

### **3. Schema Explorer**
- **Interactive table browser** with expand/collapse
- **Click-to-insert** table and column names
- **Row counts and data types** visible
- **Index and foreign key** information

### **4. Advanced Results Panel**
- **Query validation** with detailed feedback
- **Performance insights** (estimated execution time, indexes used)
- **Data preview** with export options
- **Visualization suggestions**

### **5. Query Management**
- **Query history** with timestamps
- **Bookmarked queries** for common operations
- **Learning statistics** showing AI improvements
- **Export capabilities** (CSV, JSON)

## 📦 Installation & Setup

### **Zero Dependencies Approach**
```bash
# No additional npm installs needed!
# Uses only SkeletonUI + TailwindCSS + Vue.js
```

### **Enhanced Approach** (Optional)
```bash
npm install @iconify/vue  # For comprehensive icons
npm install sortablejs    # For drag & drop query reordering
```

## 🎨 Integration Steps

### **Step 1: Add to Your Router**
```javascript
// router/index.js
{
  path: '/analytics/:workspaceId?',
  name: 'Analytics',
  component: () => import('@/views/AnalyticsWorkbench.vue'),
  meta: { requiresAuth: true }
}
```

### **Step 2: Create the Workbench View**
```vue
<!-- views/AnalyticsWorkbench.vue -->
<template>
  <SQLWorkbench
    :workspace-id="workspaceId || currentWorkspace.id"
    :tenant-id="currentUser.tenantId"
    @query-executed="trackQueryExecution"
    @schema-loaded="onSchemaLoaded"
  />
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import SQLWorkbench from '@/components/analytics/SQLWorkbench.vue'

const props = defineProps(['workspaceId'])
const { currentUser } = useAuthStore()
const { currentWorkspace } = useWorkspaceStore()

const trackQueryExecution = (data) => {
  // Track analytics events
  analytics.track('sql_query_executed', {
    workspace: data.workspaceId,
    executionTime: data.executionTime,
    rowCount: data.rowCount
  })
}
</script>
```

### **Step 3: Connect to Your Data Sources**

Replace the mock `executeSQL` function with real database connections:

```javascript
// composables/useL0L1Analytics.js
import { useDataConnection } from '@/composables/useDataConnection'

export function useL0L1Analytics() {
  const { executeQuery: dbExecuteQuery } = useDataConnection()

  const executeSQL = async (query, options = {}) => {
    // Validate with l0l1 first
    const analysis = await analyzeSQL(query, {
      validate: true,
      check_pii: true
    })

    if (!analysis.is_valid) {
      throw new Error('Query validation failed: ' + analysis.issues.join(', '))
    }

    // Use anonymized query if PII detected
    const finalQuery = analysis.pii_detected?.length > 0
      ? analysis.anonymized_query
      : query

    // Execute on your actual data warehouse
    const results = await dbExecuteQuery(finalQuery, {
      timeout: options.timeout || 30000,
      limit: options.limit || 1000
    })

    // Record successful execution for learning
    if (results.success) {
      await recordSuccessfulQuery({
        query: finalQuery,
        workspace_id: options.workspace_id,
        execution_time: results.executionTime,
        result_count: results.rowCount
      })
    }

    return results
  }

  return { executeSQL, analyzeSQL, /* ... */ }
}
```

### **Step 4: Schema Integration**

Connect your existing data warehouse schema:

```javascript
// services/schemaService.js
export class SchemaService {
  static async getWorkspaceSchema(workspaceId) {
    // Connect to your data warehouse and get schema
    const connection = await getWorkspaceConnection(workspaceId)

    const tables = await connection.query(`
      SELECT
        table_name,
        table_rows,
        table_type
      FROM information_schema.tables
      WHERE table_schema = ?
    `, [workspaceId])

    const enrichedTables = await Promise.all(
      tables.map(async (table) => {
        const columns = await connection.query(`
          SELECT
            column_name,
            data_type,
            is_nullable,
            column_key
          FROM information_schema.columns
          WHERE table_schema = ? AND table_name = ?
        `, [workspaceId, table.table_name])

        return {
          name: table.table_name,
          type: table.table_type.toLowerCase(),
          rowCount: table.table_rows?.toLocaleString() || '0',
          columns: columns.map(col => ({
            name: col.column_name,
            type: col.data_type.toUpperCase(),
            nullable: col.is_nullable === 'YES',
            primaryKey: col.column_key === 'PRI'
          }))
        }
      })
    )

    return { tables: enrichedTables }
  }
}
```

## 🎨 Customization Options

### **Theme Integration**
```css
/* Custom CSS for your brand */
.sql-workbench {
  --workbench-bg: rgb(var(--color-surface-50));
  --workbench-border: rgb(var(--color-surface-300));
  --workbench-accent: rgb(var(--color-primary-500));
}

/* Dark mode support */
.dark .sql-workbench {
  --workbench-bg: rgb(var(--color-surface-900));
  --workbench-border: rgb(var(--color-surface-600));
}
```

### **Custom Query Templates**
```javascript
const customTemplates = {
  revenue_analysis: `
SELECT
    DATE_TRUNC('month', created_at) as month,
    SUM(amount) as revenue,
    COUNT(*) as transactions,
    AVG(amount) as avg_transaction
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;`,

  user_cohort: `
SELECT
    DATE_TRUNC('month', first_order) as cohort_month,
    DATE_TRUNC('month', order_date) as order_month,
    COUNT(DISTINCT user_id) as users
FROM (
    SELECT
        user_id,
        MIN(created_at) as first_order,
        created_at as order_date
    FROM orders
    GROUP BY user_id, created_at
) cohort_data
GROUP BY cohort_month, order_month
ORDER BY cohort_month, order_month;`
}
```

### **Performance Monitoring**
```javascript
// Add to your analytics tracking
const trackQueryPerformance = (queryData) => {
  // Track slow queries
  if (queryData.executionTime > 5000) {
    analytics.track('slow_query_detected', {
      query: queryData.query.substring(0, 100),
      executionTime: queryData.executionTime,
      workspace: queryData.workspaceId
    })
  }

  // Track PII detection
  if (queryData.piiDetected?.length > 0) {
    analytics.track('pii_detected_in_query', {
      entityTypes: queryData.piiDetected.map(e => e.entity_type),
      workspace: queryData.workspaceId
    })
  }
}
```

## 🔧 Advanced Features

### **1. Query Optimization Hints**
```vue
<!-- In SQLWorkbench.vue results panel -->
<div v-if="optimizationHints.length" class="optimization-hints">
  <h4 class="font-semibold text-warning-600">⚡ Optimization Suggestions</h4>
  <ul class="text-sm space-y-1">
    <li v-for="hint in optimizationHints" :key="hint">
      • {{ hint }}
    </li>
  </ul>
</div>
```

### **2. Visual Query Builder** (Advanced)
```vue
<div class="query-builder-toggle">
  <button @click="showVisualBuilder = !showVisualBuilder"
          class="btn variant-soft-secondary">
    <iconify-icon icon="mdi:layers-triple"></iconify-icon>
    Visual Builder
  </button>
</div>

<VisualQueryBuilder
  v-if="showVisualBuilder"
  :schema="schemaData"
  @query-generated="updateQuery"
/>
```

### **3. Real-time Collaboration**
```javascript
// Add WebSocket for real-time collaboration
const { socket } = useWebSocket(`/ws/workbench/${workspaceId}`)

socket.on('query_shared', (data) => {
  // Show notification about shared query
  showToast(`${data.user} shared a query: ${data.query.substring(0, 50)}...`)
})

const shareQuery = () => {
  socket.emit('share_query', {
    query: sqlQuery.value,
    workspace: workspaceId,
    user: currentUser.name
  })
}
```

## 📊 Analytics Integration

### **Track Usage Patterns**
```javascript
// Track which features analysts use most
const trackFeatureUsage = () => {
  analytics.track('workbench_feature_used', {
    feature: 'ai_assistant',
    workspace: workspaceId,
    queryLength: sqlQuery.value.length,
    hasSchema: !!schemaContext.value
  })
}
```

### **Learning Insights Dashboard**
```vue
<div class="learning-dashboard">
  <div class="metric-card">
    <h5>Query Accuracy</h5>
    <div class="text-2xl font-bold text-success-500">
      {{ learningStats.accuracy }}%
    </div>
  </div>

  <div class="metric-card">
    <h5>Avg Performance</h5>
    <div class="text-2xl font-bold text-primary-500">
      {{ learningStats.avgExecutionTime }}ms
    </div>
  </div>

  <div class="metric-card">
    <h5>PII Prevention</h5>
    <div class="text-2xl font-bold text-warning-500">
      {{ learningStats.piiPrevented }} blocked
    </div>
  </div>
</div>
```

## 🚀 Deployment Considerations

### **Resource Management**
- **Query Timeouts**: Set appropriate timeouts for long-running analytics queries
- **Result Limits**: Prevent memory issues with large result sets
- **Caching**: Cache schema metadata and common query results

### **Security**
- **Query Validation**: Always validate queries before execution
- **PII Detection**: Block queries with detected PII in production
- **Audit Logging**: Log all executed queries for compliance

### **Performance**
- **Connection Pooling**: Use connection pools for database access
- **Async Processing**: Run long queries in background with progress updates
- **Schema Caching**: Cache schema information to reduce database calls

This workbench gives your analysts a **professional-grade SQL interface** with AI-powered assistance, making complex data analysis faster and safer while maintaining the modern look and feel of your existing dashboard.