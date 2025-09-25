<template>
  <div class="sql-workbench h-screen flex flex-col bg-surface-50-900-token">
    <!-- Top Toolbar -->
    <div class="workbench-toolbar flex items-center justify-between px-4 py-2 bg-surface-100-800-token border-b border-surface-300-600-token">
      <div class="toolbar-left flex items-center space-x-4">
        <h1 class="text-lg font-bold text-primary-600-300-token">SQL Workbench</h1>
        <div class="divider-vertical"></div>

        <!-- Workspace Selector -->
        <div class="flex items-center space-x-2">
          <iconify-icon icon="mdi:database" class="text-surface-500"></iconify-icon>
          <select class="select w-48">
            <option value="analytics">📊 Analytics Workspace</option>
            <option value="sales">💰 Sales Data</option>
            <option value="marketing">📈 Marketing Insights</option>
          </select>
        </div>

        <!-- Schema Status -->
        <div class="flex items-center space-x-2 text-sm">
          <div class="w-2 h-2 rounded-full bg-success-500"></div>
          <span class="text-surface-600-300-token">Schema Loaded</span>
        </div>
      </div>

      <div class="toolbar-right flex items-center space-x-2">
        <!-- Query History -->
        <button class="btn-icon btn-icon-sm variant-soft-surface" title="Query History">
          <iconify-icon icon="mdi:history"></iconify-icon>
        </button>

        <!-- Saved Queries -->
        <button class="btn-icon btn-icon-sm variant-soft-surface" title="Saved Queries">
          <iconify-icon icon="mdi:bookmark"></iconify-icon>
        </button>

        <!-- Export Options -->
        <button class="btn-icon btn-icon-sm variant-soft-surface" title="Export">
          <iconify-icon icon="mdi:download"></iconify-icon>
        </button>

        <div class="divider-vertical"></div>

        <!-- AI Assistant Toggle -->
        <button
          class="btn btn-sm variant-soft-primary"
          :class="{ 'variant-filled-primary': aiAssistantEnabled }"
          @click="aiAssistantEnabled = !aiAssistantEnabled"
        >
          <iconify-icon icon="mdi:robot"></iconify-icon>
          <span>AI Assistant</span>
        </button>
      </div>
    </div>

    <div class="workbench-content flex flex-1 min-h-0">
      <!-- Left Sidebar - Schema Browser -->
      <div class="schema-browser w-64 bg-surface-100-800-token border-r border-surface-300-600-token flex flex-col">
        <div class="schema-header p-3 border-b border-surface-300-600-token">
          <h3 class="font-semibold text-sm flex items-center">
            <iconify-icon icon="mdi:file-tree" class="mr-2"></iconify-icon>
            Database Schema
          </h3>
        </div>

        <div class="schema-tree flex-1 overflow-y-auto p-2">
          <div class="space-y-1">
            <!-- Tables -->
            <details open class="group">
              <summary class="flex items-center p-2 text-sm font-medium cursor-pointer hover:bg-surface-200-700-token rounded">
                <iconify-icon icon="mdi:chevron-down" class="mr-1 transition-transform group-open:rotate-0 rotate-270"></iconify-icon>
                <iconify-icon icon="mdi:table" class="mr-2 text-primary-500"></iconify-icon>
                Tables (8)
              </summary>
              <div class="ml-4 space-y-1">
                <div v-for="table in tables" :key="table.name" class="table-item">
                  <div class="flex items-center p-1 text-xs hover:bg-surface-200-700-token rounded cursor-pointer" @click="insertTableName(table.name)">
                    <iconify-icon icon="mdi:table-large" class="mr-2 text-surface-500"></iconify-icon>
                    <span class="font-mono">{{ table.name }}</span>
                    <span class="ml-auto text-surface-400-500-token">({{ table.rowCount }})</span>
                  </div>
                  <!-- Columns -->
                  <div v-if="expandedTables.includes(table.name)" class="ml-4 mt-1 space-y-1">
                    <div v-for="column in table.columns" :key="column.name"
                         class="flex items-center p-1 text-xs text-surface-600-300-token hover:bg-surface-200-700-token rounded cursor-pointer"
                         @click="insertColumnName(table.name, column.name)">
                      <iconify-icon :icon="getColumnIcon(column.type)" class="mr-2"></iconify-icon>
                      <span class="font-mono">{{ column.name }}</span>
                      <span class="ml-auto text-xs">{{ column.type }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </details>

            <!-- Views -->
            <details class="group">
              <summary class="flex items-center p-2 text-sm font-medium cursor-pointer hover:bg-surface-200-700-token rounded">
                <iconify-icon icon="mdi:chevron-right" class="mr-1 transition-transform group-open:rotate-90"></iconify-icon>
                <iconify-icon icon="mdi:eye" class="mr-2 text-secondary-500"></iconify-icon>
                Views (3)
              </summary>
            </details>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="main-content flex-1 flex flex-col min-w-0">
        <!-- Query Editor -->
        <div class="query-editor flex-1 flex flex-col">
          <!-- Editor Toolbar -->
          <div class="editor-toolbar flex items-center justify-between px-4 py-2 bg-surface-50-950-token border-b border-surface-300-600-token">
            <div class="flex items-center space-x-2">
              <span class="text-sm font-medium">Query Editor</span>

              <!-- Query Templates -->
              <select class="select select-sm w-40" @change="loadTemplate">
                <option value="">Quick Templates</option>
                <option value="select_all">SELECT * FROM table</option>
                <option value="group_by">GROUP BY Analysis</option>
                <option value="join">JOIN Tables</option>
                <option value="window">Window Functions</option>
              </select>
            </div>

            <div class="flex items-center space-x-2">
              <!-- Format SQL -->
              <button class="btn btn-sm variant-soft-surface" @click="formatSQL">
                <iconify-icon icon="mdi:code-braces"></iconify-icon>
                <span>Format</span>
              </button>

              <!-- Run Query -->
              <button
                class="btn btn-sm variant-filled-primary"
                @click="executeQuery"
                :disabled="!sqlQuery.trim() || isExecuting"
              >
                <iconify-icon v-if="isExecuting" icon="mdi:loading" class="animate-spin"></iconify-icon>
                <iconify-icon v-else icon="mdi:play"></iconify-icon>
                <span>{{ isExecuting ? 'Running...' : 'Run Query' }}</span>
                <kbd class="kbd kbd-sm ml-2">F5</kbd>
              </button>
            </div>
          </div>

          <!-- SQL Editor Area -->
          <div class="editor-area flex-1 relative">
            <textarea
              ref="sqlEditor"
              class="w-full h-full p-4 font-mono text-sm bg-surface-50-950-token text-surface-900-50-token resize-none border-0 focus:ring-0"
              placeholder="-- Enter your SQL query here
-- Press F5 or click 'Run Query' to execute
-- The AI assistant will help with suggestions and validation

SELECT
    users.name,
    users.email,
    COUNT(orders.id) as total_orders,
    SUM(orders.amount) as total_spent
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE users.created_at >= '2024-01-01'
GROUP BY users.id, users.name, users.email
ORDER BY total_spent DESC
LIMIT 10;"
              v-model="sqlQuery"
              @keydown="handleKeydown"
              @input="onQueryChange"
            ></textarea>

            <!-- Line Numbers -->
            <div class="line-numbers absolute left-0 top-0 p-4 text-xs text-surface-400-600-token font-mono pointer-events-none">
              <div v-for="n in lineCount" :key="n" class="leading-5">{{ n }}</div>
            </div>

            <!-- AI Assistant Panel -->
            <div v-if="aiAssistantEnabled" class="ai-assistant absolute top-4 right-4 w-80 max-h-96 bg-surface-100-800-token border border-surface-300-600-token rounded-lg shadow-lg">
              <div class="p-3 border-b border-surface-300-600-token">
                <h4 class="font-semibold text-sm flex items-center">
                  <iconify-icon icon="mdi:robot" class="mr-2 text-primary-500"></iconify-icon>
                  AI Assistant
                </h4>
              </div>

              <div class="p-3 space-y-2 max-h-64 overflow-y-auto">
                <!-- Live Analysis -->
                <div v-if="liveAnalysis.pii_detected?.length" class="alert alert-sm variant-soft-warning">
                  <iconify-icon icon="mdi:shield-alert"></iconify-icon>
                  <span class="text-xs">PII detected in query</span>
                </div>

                <div v-if="liveAnalysis.suggestions?.length" class="space-y-1">
                  <div class="text-xs font-medium text-surface-600-300-token">Suggestions:</div>
                  <div v-for="suggestion in liveAnalysis.suggestions.slice(0, 3)" :key="suggestion"
                       class="text-xs p-2 bg-primary-50-900-token rounded cursor-pointer hover:bg-primary-100-800-token"
                       @click="applySuggestion(suggestion)">
                    {{ suggestion }}
                  </div>
                </div>

                <!-- Query Completion -->
                <div v-if="queryCompletions.length" class="space-y-1">
                  <div class="text-xs font-medium text-surface-600-300-token">Auto-complete:</div>
                  <div v-for="completion in queryCompletions" :key="completion"
                       class="text-xs p-2 bg-surface-50-900-token rounded cursor-pointer hover:bg-surface-100-800-token font-mono"
                       @click="applyCompletion(completion)">
                    {{ completion }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Results Panel -->
        <div class="results-panel flex-1 border-t border-surface-300-600-token bg-surface-50-950-token">
          <div class="results-toolbar flex items-center justify-between px-4 py-2 border-b border-surface-300-600-token">
            <div class="flex items-center space-x-4">
              <h3 class="font-semibold text-sm">Results</h3>

              <div v-if="queryResults" class="text-xs text-surface-600-300-token">
                {{ queryResults.rowCount }} rows • {{ queryResults.executionTime }}ms
              </div>
            </div>

            <div v-if="queryResults" class="flex items-center space-x-2">
              <!-- Export Results -->
              <button class="btn btn-sm variant-soft-surface">
                <iconify-icon icon="mdi:download"></iconify-icon>
                <span>Export CSV</span>
              </button>

              <!-- Visualize -->
              <button class="btn btn-sm variant-soft-secondary">
                <iconify-icon icon="mdi:chart-line"></iconify-icon>
                <span>Visualize</span>
              </button>
            </div>
          </div>

          <!-- Results Content -->
          <div class="results-content flex-1 overflow-auto p-4">
            <!-- Analysis Results -->
            <div v-if="analysisResults && !queryResults" class="analysis-results space-y-4">
              <!-- Validation Status -->
              <div class="card variant-soft">
                <div class="card-header pb-2">
                  <h4 class="h4 flex items-center">
                    <iconify-icon :icon="analysisResults.is_valid ? 'mdi:check-circle' : 'mdi:alert-circle'"
                                  :class="analysisResults.is_valid ? 'text-success-500' : 'text-error-500'"
                                  class="mr-2"></iconify-icon>
                    Query Validation
                  </h4>
                </div>
                <div class="p-4 pt-0">
                  <div v-if="analysisResults.is_valid" class="text-success-600-300-token">
                    ✅ Query syntax and structure look good
                  </div>
                  <div v-else class="space-y-2">
                    <div v-for="issue in analysisResults.issues" :key="issue" class="text-error-600-300-token text-sm">
                      • {{ issue }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- PII Detection -->
              <div v-if="analysisResults.pii_detected?.length" class="card variant-soft-warning">
                <div class="card-header pb-2">
                  <h4 class="h4 flex items-center">
                    <iconify-icon icon="mdi:shield-alert" class="mr-2 text-warning-500"></iconify-icon>
                    Privacy Alert
                  </h4>
                </div>
                <div class="p-4 pt-0">
                  <div class="text-sm mb-2">Detected potential PII in your query:</div>
                  <div class="space-y-1">
                    <div v-for="entity in analysisResults.pii_detected" :key="entity.text"
                         class="inline-flex items-center px-2 py-1 bg-warning-100-800-token text-warning-800-100-token rounded text-xs mr-2">
                      <iconify-icon :icon="getPiiIcon(entity.entity_type)" class="mr-1"></iconify-icon>
                      {{ entity.entity_type }}: {{ entity.text }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Performance Insights -->
              <div class="card variant-soft-secondary">
                <div class="card-header pb-2">
                  <h4 class="h4 flex items-center">
                    <iconify-icon icon="mdi:speedometer" class="mr-2 text-secondary-500"></iconify-icon>
                    Performance Insights
                  </h4>
                </div>
                <div class="p-4 pt-0 space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span>Estimated rows to scan:</span>
                    <span class="font-mono">~1.2M</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span>Indexes used:</span>
                    <span class="text-success-600-300-token">users_created_at_idx</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span>Estimated execution:</span>
                    <span class="font-mono">~150ms</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Data Results Table -->
            <div v-if="queryResults" class="data-results">
              <div class="overflow-x-auto">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th v-for="column in queryResults.columns" :key="column" class="font-mono text-xs">
                        {{ column }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, index) in queryResults.data.slice(0, 100)" :key="index">
                      <td v-for="column in queryResults.columns" :key="column" class="font-mono text-xs">
                        {{ formatCellValue(row[column]) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="!analysisResults && !queryResults" class="empty-state text-center py-12">
              <iconify-icon icon="mdi:database-search" class="text-6xl text-surface-300-600-token mb-4"></iconify-icon>
              <h3 class="h3 mb-2">Ready for Analysis</h3>
              <p class="text-surface-600-300-token">Write your SQL query above and click 'Run Query' to see results and analysis</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Sidebar - Graph Intelligence -->
      <div class="graph-intelligence w-80 bg-surface-100-800-token border-l border-surface-300-600-token flex flex-col">
        <!-- Tabs for different insights -->
        <div class="insight-tabs flex border-b border-surface-300-600-token">
          <button
            v-for="tab in insightTabs"
            :key="tab.id"
            class="flex-1 p-2 text-xs font-medium transition-colors"
            :class="activeInsightTab === tab.id ? 'bg-primary-500 text-white' : 'text-surface-600-300-token hover:bg-surface-200-700-token'"
            @click="activeInsightTab = tab.id">
            <iconify-icon :icon="tab.icon" class="mr-1"></iconify-icon>
            {{ tab.label }}
          </button>
        </div>

        <div class="insight-content flex-1 overflow-y-auto p-3">
          <!-- Workspace Intelligence Tab -->
          <div v-if="activeInsightTab === 'workspace'" class="space-y-4">
            <!-- Most Used Tables -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:table-star" class="mr-2 text-primary-500"></iconify-icon>
                Popular Tables
              </h4>
              <div class="space-y-2">
                <div v-for="(usage, table) in workspaceInsights?.most_used_tables" :key="table"
                     class="flex items-center justify-between text-xs">
                  <div class="flex items-center cursor-pointer hover:text-primary-500" @click="insertTableName(table)">
                    <iconify-icon icon="mdi:table" class="mr-2 text-surface-500"></iconify-icon>
                    <span class="font-mono">{{ table }}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div class="w-12 bg-surface-200-700-token h-1 rounded">
                      <div class="bg-primary-500 h-1 rounded" :style="{ width: Math.min(100, (usage / Math.max(...Object.values(workspaceInsights?.most_used_tables || {}))) * 100) + '%' }"></div>
                    </div>
                    <span class="text-surface-400-600-token font-mono">{{ usage }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Performance Distribution -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:speedometer" class="mr-2 text-secondary-500"></iconify-icon>
                Query Performance
              </h4>
              <div class="space-y-2 text-xs">
                <div class="flex items-center justify-between">
                  <span class="flex items-center">
                    <div class="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                    Fast (&lt;100ms)
                  </span>
                  <span class="font-mono">{{ workspaceInsights?.performance_distribution?.fast || 0 }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center">
                    <div class="w-2 h-2 bg-warning-500 rounded-full mr-2"></div>
                    Medium (100-1000ms)
                  </span>
                  <span class="font-mono">{{ workspaceInsights?.performance_distribution?.medium || 0 }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="flex items-center">
                    <div class="w-2 h-2 bg-error-500 rounded-full mr-2"></div>
                    Slow (&gt;1000ms)
                  </span>
                  <span class="font-mono">{{ workspaceInsights?.performance_distribution?.slow || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Learning Stats -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:brain" class="mr-2 text-tertiary-500"></iconify-icon>
                Intelligence
              </h4>
              <dl class="space-y-2 text-xs">
                <div class="flex justify-between">
                  <dt>Total Patterns:</dt>
                  <dd class="font-mono">{{ workspaceInsights?.total_queries_analyzed || 0 }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt>Unique Tables:</dt>
                  <dd class="font-mono">{{ workspaceInsights?.unique_tables || 0 }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt>Complexity Trend:</dt>
                  <dd class="font-mono capitalize text-primary-600-300-token">{{ workspaceInsights?.complexity_trends?.trend || 'stable' }}</dd>
                </div>
              </dl>
            </div>
          </div>

          <!-- Relationships Tab -->
          <div v-if="activeInsightTab === 'relationships'" class="space-y-4">
            <!-- Table Relationships -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:graph" class="mr-2 text-success-500"></iconify-icon>
                Table Relationships
              </h4>
              <div class="space-y-3">
                <div v-for="relationship in tableRelationships" :key="relationship.id" class="relationship-item">
                  <div class="flex items-center text-xs mb-1">
                    <span class="font-mono text-primary-600-300-token">{{ relationship.from_table }}</span>
                    <iconify-icon icon="mdi:arrow-right" class="mx-2 text-surface-400-600-token"></iconify-icon>
                    <span class="font-mono text-secondary-600-300-token">{{ relationship.to_table }}</span>
                  </div>
                  <div class="ml-4 text-xs text-surface-500">
                    <div class="flex items-center justify-between">
                      <span>{{ relationship.join_pattern }}</span>
                      <span class="confidence-badge px-1 py-0.5 bg-success-100-800-token text-success-800-100-token rounded text-xs">{{ (relationship.confidence * 100).toFixed(0) }}%</span>
                    </div>
                    <div class="text-surface-400-600-token mt-1">Used {{ relationship.frequency }} times</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Recommended Joins -->
            <div v-if="recommendedJoins.length" class="card variant-soft-primary p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:link-variant" class="mr-2 text-primary-500"></iconify-icon>
                Suggested Joins
              </h4>
              <div class="space-y-2">
                <div v-for="join in recommendedJoins" :key="join.id"
                     class="p-2 bg-primary-50-900-token rounded cursor-pointer hover:bg-primary-100-800-token"
                     @click="applySuggestion(join.sql)">
                  <div class="font-mono text-xs text-primary-700-200-token">{{ join.sql }}</div>
                  <div class="text-xs text-primary-600-300-token mt-1">{{ join.reason }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Performance Tab -->
          <div v-if="activeInsightTab === 'performance'" class="space-y-4">
            <!-- Performance Patterns -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:chart-line" class="mr-2 text-warning-500"></iconify-icon>
                Performance Insights
              </h4>
              <div class="space-y-3">
                <div v-for="insight in performanceInsights" :key="insight.id" class="performance-insight">
                  <div class="flex items-start space-x-2">
                    <iconify-icon :icon="getPerformanceIcon(insight.type)"
                                  :class="getPerformanceColor(insight.type)"
                                  class="mt-0.5"></iconify-icon>
                    <div class="flex-1">
                      <div class="text-xs font-medium">{{ insight.title }}</div>
                      <div class="text-xs text-surface-500 mt-1">{{ insight.description }}</div>
                      <div v-if="insight.suggestion" class="text-xs text-primary-600-300-token mt-1 cursor-pointer hover:underline"
                           @click="applySuggestion(insight.suggestion)">💡 {{ insight.suggestion_text }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Optimization Opportunities -->
            <div v-if="optimizationOpportunities.length" class="card variant-soft-warning p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:lightbulb" class="mr-2 text-warning-500"></iconify-icon>
                Optimizations
              </h4>
              <div class="space-y-2">
                <div v-for="opportunity in optimizationOpportunities" :key="opportunity.id"
                     class="p-2 bg-warning-50-900-token rounded text-xs">
                  <div class="font-medium text-warning-800-100-token">{{ opportunity.title }}</div>
                  <div class="text-warning-700-200-token mt-1">{{ opportunity.description }}</div>
                  <div v-if="opportunity.impact" class="text-xs text-warning-600-300-token mt-1">
                    Expected improvement: {{ opportunity.impact }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Team Patterns Tab -->
          <div v-if="activeInsightTab === 'team'" class="space-y-4">
            <!-- Department Patterns -->
            <div class="card variant-soft p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:account-group" class="mr-2 text-tertiary-500"></iconify-icon>
                Team Patterns
              </h4>
              <div class="space-y-3">
                <div v-for="(patterns, department) in teamPatterns" :key="department" class="department-patterns">
                  <div class="flex items-center mb-2">
                    <iconify-icon :icon="getDepartmentIcon(department)" class="mr-2 text-surface-500"></iconify-icon>
                    <span class="text-xs font-medium capitalize">{{ department }}</span>
                  </div>
                  <div class="ml-6 space-y-1">
                    <div v-for="pattern in patterns.slice(0, 3)" :key="pattern"
                         class="text-xs text-surface-600-300-token cursor-pointer hover:text-primary-500"
                         @click="loadPatternTemplate(department, pattern)">
                      • {{ pattern }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Common Templates -->
            <div class="card variant-soft-tertiary p-3">
              <h4 class="font-medium text-sm mb-3 flex items-center">
                <iconify-icon icon="mdi:file-document-multiple" class="mr-2 text-tertiary-500"></iconify-icon>
                Popular Templates
              </h4>
              <div class="space-y-2">
                <div v-for="template in popularTemplates" :key="template.id"
                     class="p-2 bg-tertiary-50-900-token rounded cursor-pointer hover:bg-tertiary-100-800-token"
                     @click="loadQuery(template.sql)">
                  <div class="text-xs font-medium text-tertiary-800-100-token">{{ template.name }}</div>
                  <div class="text-xs text-tertiary-600-300-token mt-1">Used {{ template.usage_count }} times</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Bar -->
    <div class="status-bar flex items-center justify-between px-4 py-1 bg-surface-200-700-token border-t border-surface-300-600-token text-xs">
      <div class="flex items-center space-x-4">
        <span class="flex items-center">
          <div class="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
          Connected to Analytics DB
        </span>
        <span>{{ tables.length }} tables loaded</span>
      </div>
      <div class="flex items-center space-x-4">
        <span>Line {{ currentLine }}, Column {{ currentColumn }}</span>
        <span>{{ sqlQuery.length }} characters</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useL0L1Analytics } from '@/composables/useL0L1Analytics'

// Graph intelligence state
const activeInsightTab = ref('workspace')
const workspaceInsights = ref(null)
const tableRelationships = ref([])
const recommendedJoins = ref([])
const performanceInsights = ref([])
const optimizationOpportunities = ref([])
const teamPatterns = ref({})
const popularTemplates = ref([])

// Tab configuration
const insightTabs = [
  { id: 'workspace', label: 'Workspace', icon: 'mdi:view-dashboard' },
  { id: 'relationships', label: 'Relations', icon: 'mdi:graph' },
  { id: 'performance', label: 'Performance', icon: 'mdi:speedometer' },
  { id: 'team', label: 'Team', icon: 'mdi:account-group' }
]

const {
  analyzeSQL,
  executeSQL,
  getLearningStats,
  getRecentQueries,
  getWorkspaceInsights,
  getGraphIntelligence,
  isLoading
} = useL0L1Analytics()

// Editor state
const sqlQuery = ref('')
const sqlEditor = ref(null)
const currentLine = ref(1)
const currentColumn = ref(1)

// UI state
const aiAssistantEnabled = ref(true)
const expandedTables = ref(['users', 'orders'])

// Analysis results
const analysisResults = ref(null)
const queryResults = ref(null)
const liveAnalysis = ref({})
const queryCompletions = ref([])
const learningStats = ref(null)
const recentQueries = ref([])
const isExecuting = ref(false)

// Mock data - replace with real data from your backend
const tables = ref([
  {
    name: 'users',
    rowCount: '1.2M',
    columns: [
      { name: 'id', type: 'INTEGER' },
      { name: 'name', type: 'VARCHAR' },
      { name: 'email', type: 'VARCHAR' },
      { name: 'created_at', type: 'TIMESTAMP' }
    ]
  },
  {
    name: 'orders',
    rowCount: '5.8M',
    columns: [
      { name: 'id', type: 'INTEGER' },
      { name: 'user_id', type: 'INTEGER' },
      { name: 'amount', type: 'DECIMAL' },
      { name: 'status', type: 'VARCHAR' },
      { name: 'created_at', type: 'TIMESTAMP' }
    ]
  }
])

const lineCount = computed(() => {
  return sqlQuery.value.split('\n').length
})

// Methods
const handleKeydown = (event) => {
  if (event.key === 'F5') {
    event.preventDefault()
    executeQuery()
  }

  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    executeQuery()
  }

  // Update cursor position
  updateCursorPosition()
}

const updateCursorPosition = () => {
  if (!sqlEditor.value) return

  const textarea = sqlEditor.value
  const start = textarea.selectionStart
  const textBeforeCursor = sqlQuery.value.substring(0, start)

  currentLine.value = textBeforeCursor.split('\n').length
  currentColumn.value = textBeforeCursor.split('\n').pop().length + 1
}

const onQueryChange = () => {
  // Live analysis (debounced)
  if (aiAssistantEnabled.value && sqlQuery.value.trim()) {
    debouncedAnalyze()
  }
}

let analyzeTimeout
const debouncedAnalyze = () => {
  clearTimeout(analyzeTimeout)
  analyzeTimeout = setTimeout(async () => {
    try {
      const results = await analyzeSQL(sqlQuery.value, {
        validate: true,
        check_pii: true,
        complete: true
      })
      liveAnalysis.value = results
    } catch (error) {
      console.error('Live analysis failed:', error)
    }
  }, 1000)
}

const executeQuery = async () => {
  if (!sqlQuery.value.trim() || isExecuting.value) return

  isExecuting.value = true

  try {
    // First analyze the query
    analysisResults.value = await analyzeSQL(sqlQuery.value, {
      validate: true,
      explain: true,
      check_pii: true
    })

    // If valid, execute it (mock for now)
    if (analysisResults.value.is_valid) {
      // Mock query execution - replace with real execution
      queryResults.value = {
        columns: ['name', 'email', 'total_orders', 'total_spent'],
        data: [
          { name: 'John Doe', email: 'john@example.com', total_orders: 15, total_spent: 1250.50 },
          { name: 'Jane Smith', email: 'jane@example.com', total_orders: 23, total_spent: 2100.75 }
        ],
        rowCount: 2,
        executionTime: 142
      }
    }

  } catch (error) {
    console.error('Query execution failed:', error)
  } finally {
    isExecuting.value = false
  }
}

const formatSQL = () => {
  // Simple SQL formatting - replace with proper formatter
  const formatted = sqlQuery.value
    .replace(/\bSELECT\b/gi, 'SELECT')
    .replace(/\bFROM\b/gi, '\nFROM')
    .replace(/\bWHERE\b/gi, '\nWHERE')
    .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
    .replace(/\bORDER BY\b/gi, '\nORDER BY')

  sqlQuery.value = formatted
}

const insertTableName = (tableName) => {
  const textarea = sqlEditor.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd

  const textBefore = sqlQuery.value.substring(0, start)
  const textAfter = sqlQuery.value.substring(end)

  sqlQuery.value = textBefore + tableName + textAfter

  // Move cursor after inserted text
  setTimeout(() => {
    textarea.focus()
    textarea.setSelectionRange(start + tableName.length, start + tableName.length)
  }, 0)
}

const insertColumnName = (tableName, columnName) => {
  insertTableName(`${tableName}.${columnName}`)
}

const getColumnIcon = (type) => {
  const iconMap = {
    'INTEGER': 'mdi:numeric',
    'VARCHAR': 'mdi:format-text',
    'TEXT': 'mdi:text',
    'TIMESTAMP': 'mdi:clock',
    'DECIMAL': 'mdi:decimal',
    'BOOLEAN': 'mdi:check-box-outline'
  }
  return iconMap[type] || 'mdi:database-outline'
}

const getPiiIcon = (entityType) => {
  const iconMap = {
    'EMAIL_ADDRESS': 'mdi:email',
    'PHONE_NUMBER': 'mdi:phone',
    'PERSON': 'mdi:account',
    'SSN': 'mdi:shield-alert'
  }
  return iconMap[entityType] || 'mdi:alert'
}

const formatCellValue = (value) => {
  if (value === null || value === undefined) return 'NULL'
  if (typeof value === 'number') return value.toLocaleString()
  return String(value)
}

const loadQuery = (sql) => {
  sqlQuery.value = sql
  sqlEditor.value?.focus()
}

const loadTemplate = (event) => {
  const template = event.target.value
  if (!template) return

  const templates = {
    select_all: 'SELECT *\nFROM table_name\nLIMIT 100;',
    group_by: 'SELECT \n    column1,\n    COUNT(*) as count\nFROM table_name\nGROUP BY column1\nORDER BY count DESC;',
    join: 'SELECT \n    t1.column1,\n    t2.column2\nFROM table1 t1\nJOIN table2 t2 ON t1.id = t2.table1_id;',
    window: 'SELECT \n    column1,\n    ROW_NUMBER() OVER (PARTITION BY column1 ORDER BY column2) as row_num\nFROM table_name;'
  }

  if (templates[template]) {
    sqlQuery.value = templates[template]
    event.target.value = '' // Reset dropdown
  }
}

// Graph intelligence methods
const getPerformanceIcon = (type) => {
  const iconMap = {
    'slow_table': 'mdi:table-clock',
    'missing_index': 'mdi:index',
    'large_scan': 'mdi:magnify-scan',
    'optimization': 'mdi:rocket-launch'
  }
  return iconMap[type] || 'mdi:information'
}

const getPerformanceColor = (type) => {
  const colorMap = {
    'slow_table': 'text-error-500',
    'missing_index': 'text-warning-500',
    'large_scan': 'text-warning-500',
    'optimization': 'text-success-500'
  }
  return colorMap[type] || 'text-surface-500'
}

const getDepartmentIcon = (department) => {
  const iconMap = {
    'sales': 'mdi:currency-usd',
    'marketing': 'mdi:bullhorn',
    'finance': 'mdi:calculator',
    'engineering': 'mdi:code-braces',
    'analytics': 'mdi:chart-bar'
  }
  return iconMap[department.toLowerCase()] || 'mdi:account-group'
}

const loadPatternTemplate = (department, pattern) => {
  // Load department-specific query templates
  const templates = {
    sales: {
      'revenue_analysis': 'SELECT DATE_TRUNC(\'month\', created_at) as month, SUM(amount) as revenue FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL \'12 months\' GROUP BY 1 ORDER BY 1;',
      'customer_segmentation': 'SELECT user_id, COUNT(*) as order_count, SUM(amount) as total_spent FROM orders GROUP BY user_id HAVING COUNT(*) > 5;'
    },
    marketing: {
      'campaign_performance': 'SELECT campaign_id, COUNT(DISTINCT user_id) as unique_users, SUM(conversion_value) as total_value FROM events WHERE event_type = \'conversion\' GROUP BY campaign_id;',
      'funnel_analysis': 'SELECT step, COUNT(*) as users FROM funnel_events GROUP BY step ORDER BY step;'
    }
  }

  const template = templates[department]?.[pattern.toLowerCase().replace(/ /g, '_')]
  if (template) {
    sqlQuery.value = template
  }
}

const applySuggestion = (suggestion) => {
  if (typeof suggestion === 'string') {
    // If it's a SQL string, replace or append to current query
    if (sqlQuery.value.trim()) {
      sqlQuery.value += '\n' + suggestion
    } else {
      sqlQuery.value = suggestion
    }
  }
  sqlEditor.value?.focus()
}

const loadGraphIntelligence = async () => {
  try {
    const intelligence = await getGraphIntelligence('analytics')

    // Update workspace insights
    workspaceInsights.value = intelligence.workspace_insights

    // Update table relationships
    tableRelationships.value = intelligence.table_relationships || [
      {
        id: 1,
        from_table: 'users',
        to_table: 'orders',
        join_pattern: 'users.id = orders.user_id',
        confidence: 0.95,
        frequency: 143
      },
      {
        id: 2,
        from_table: 'orders',
        to_table: 'order_items',
        join_pattern: 'orders.id = order_items.order_id',
        confidence: 0.88,
        frequency: 89
      }
    ]

    // Update recommended joins based on current query context
    recommendedJoins.value = intelligence.recommended_joins || [
      {
        id: 1,
        sql: 'JOIN orders ON users.id = orders.user_id',
        reason: 'Commonly used with users table'
      }
    ]

    // Update performance insights
    performanceInsights.value = intelligence.performance_insights || [
      {
        id: 1,
        type: 'slow_table',
        title: 'Large table scan on orders',
        description: 'Queries on orders table average 1.2s',
        suggestion: 'WHERE orders.created_at > \'2024-01-01\'',
        suggestion_text: 'Add date filter to reduce scan'
      },
      {
        id: 2,
        type: 'missing_index',
        title: 'Missing index opportunity',
        description: 'created_at column frequently filtered',
        suggestion_text: 'Consider adding index on created_at'
      }
    ]

    // Update optimization opportunities
    optimizationOpportunities.value = intelligence.optimization_opportunities || [
      {
        id: 1,
        title: 'Add LIMIT clause',
        description: 'Large result sets detected in similar queries',
        impact: '60% faster execution'
      }
    ]

    // Update team patterns
    teamPatterns.value = intelligence.team_patterns || {
      sales: ['Revenue analysis', 'Customer segmentation', 'Conversion tracking'],
      marketing: ['Campaign performance', 'Funnel analysis', 'Attribution modeling'],
      finance: ['Cost analysis', 'Budget tracking', 'Churn analysis']
    }

    // Update popular templates
    popularTemplates.value = intelligence.popular_templates || [
      {
        id: 1,
        name: 'User Order Summary',
        sql: 'SELECT u.name, COUNT(o.id) as orders, SUM(o.amount) as total FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id;',
        usage_count: 47
      },
      {
        id: 2,
        name: 'Monthly Revenue',
        sql: 'SELECT DATE_TRUNC(\'month\', created_at) as month, SUM(amount) as revenue FROM orders GROUP BY 1 ORDER BY 1;',
        usage_count: 32
      }
    ]

  } catch (error) {
    console.error('Failed to load graph intelligence:', error)
    // Set fallback data
    workspaceInsights.value = {
      most_used_tables: { users: 156, orders: 142, products: 89 },
      performance_distribution: { fast: 45, medium: 32, slow: 8 },
      total_queries_analyzed: 234,
      unique_tables: 12,
      complexity_trends: { trend: 'increasing' }
    }
  }
}

onMounted(async () => {
  // Load initial data
  try {
    learningStats.value = await getLearningStats('analytics')
    recentQueries.value = await getRecentQueries()

    // Load graph-based intelligence
    await loadGraphIntelligence()
  } catch (error) {
    console.error('Failed to load initial data:', error)
  }
})

// Watch for query changes to update relationship suggestions
watch(sqlQuery, async (newQuery) => {
  if (newQuery && activeInsightTab.value === 'relationships') {
    // Update recommended joins based on current query
    // This would typically call an API to get context-aware suggestions
    // For now, we'll simulate this behavior
  }
})
</script>

<style scoped>
.sql-workbench {
  font-family: system-ui, -apple-system, sans-serif;
}

.line-numbers {
  width: 3rem;
  border-right: 1px solid rgb(var(--color-surface-300) / var(--color-surface-600));
  background: rgb(var(--color-surface-100) / var(--color-surface-800));
}

.query-editor textarea {
  padding-left: 4rem; /* Space for line numbers */
}

.schema-tree details[open] summary iconify-icon {
  transform: rotate(90deg);
}

.table-item:hover .table-name {
  background: rgb(var(--color-surface-200) / var(--color-surface-700));
}

/* Scrollbar styling */
.schema-tree::-webkit-scrollbar,
.results-content::-webkit-scrollbar {
  width: 6px;
}

.schema-tree::-webkit-scrollbar-track,
.results-content::-webkit-scrollbar-track {
  background: rgb(var(--color-surface-100));
}

.schema-tree::-webkit-scrollbar-thumb,
.results-content::-webkit-scrollbar-thumb {
  background: rgb(var(--color-surface-400));
  border-radius: 3px;
}
</style>