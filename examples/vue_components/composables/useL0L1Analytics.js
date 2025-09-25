import { ref } from 'vue'

const API_BASE = '/api'

export function useL0L1Analytics() {
  const isLoading = ref(false)
  const error = ref(null)

  const apiCall = async (endpoint, options = {}) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // SQL Analysis
  const analyzeSQL = async (query, options = {}) => {
    const results = {}

    // Validate query if requested
    if (options.validate) {
      const validation = await apiCall('/sql/validate', {
        method: 'POST',
        body: JSON.stringify({
          query,
          schema_context: options.schema_context,
          workspace_id: options.workspace_id
        })
      })
      Object.assign(results, validation)
    }

    // Check for PII if requested
    if (options.check_pii) {
      const piiResults = await apiCall('/sql/check-pii', {
        method: 'POST',
        body: JSON.stringify({ query })
      })
      results.pii_detected = piiResults.entities
      results.anonymized_query = piiResults.anonymized_query
    }

    // Get explanation if requested
    if (options.explain) {
      const explanation = await apiCall('/sql/explain', {
        method: 'POST',
        body: JSON.stringify({
          query,
          schema_context: options.schema_context
        })
      })
      results.explanation = explanation.explanation
    }

    // Get completion suggestions if requested
    if (options.complete) {
      try {
        const completion = await apiCall('/sql/complete', {
          method: 'POST',
          body: JSON.stringify({
            partial_query: query,
            schema_context: options.schema_context,
            workspace_id: options.workspace_id,
            max_suggestions: 3
          })
        })
        results.suggestions = completion.suggestions
        results.learning_applied = completion.learning_applied
      } catch (err) {
        // Completion is optional, don't fail the whole analysis
        results.suggestions = []
      }
    }

    return results
  }

  // Execute SQL Query (mock implementation - replace with real execution)
  const executeSQL = async (query, options = {}) => {
    // In a real implementation, this would connect to your data warehouse
    // For now, we'll mock the execution after validation

    const analysis = await analyzeSQL(query, { validate: true, check_pii: true })

    if (!analysis.is_valid) {
      throw new Error('Query validation failed: ' + analysis.issues.join(', '))
    }

    if (analysis.pii_detected?.length > 0) {
      console.warn('PII detected in query - using anonymized version for execution')
      query = analysis.anonymized_query || query
    }

    // Mock execution - replace with actual database execution
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500))

    // Mock result based on query type
    if (query.toLowerCase().includes('select')) {
      return generateMockResults(query)
    } else {
      return {
        success: true,
        message: 'Query executed successfully',
        rowsAffected: Math.floor(Math.random() * 1000),
        executionTime: Math.floor(Math.random() * 500 + 50)
      }
    }
  }

  // Generate mock results for demo purposes
  const generateMockResults = (query) => {
    const mockData = generateMockDataFromQuery(query)

    return {
      columns: mockData.columns,
      data: mockData.rows,
      rowCount: mockData.rows.length,
      executionTime: Math.floor(Math.random() * 300 + 50),
      totalRows: mockData.rows.length + Math.floor(Math.random() * 10000),
      hasMore: Math.random() > 0.7
    }
  }

  const generateMockDataFromQuery = (query) => {
    // Simple query parsing to generate relevant mock data
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes('users')) {
      return {
        columns: ['id', 'name', 'email', 'created_at'],
        rows: Array.from({ length: 50 }, (_, i) => ({
          id: i + 1,
          name: `User ${i + 1}`,
          email: `user${i + 1}@example.com`,
          created_at: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        }))
      }
    }

    if (lowerQuery.includes('orders')) {
      return {
        columns: ['id', 'user_id', 'amount', 'status', 'created_at'],
        rows: Array.from({ length: 75 }, (_, i) => ({
          id: i + 1000,
          user_id: Math.floor(Math.random() * 50) + 1,
          amount: (Math.random() * 1000 + 10).toFixed(2),
          status: ['pending', 'completed', 'cancelled'][Math.floor(Math.random() * 3)],
          created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        }))
      }
    }

    // Default mock data
    return {
      columns: ['column1', 'column2', 'column3'],
      rows: Array.from({ length: 25 }, (_, i) => ({
        column1: `Value ${i + 1}`,
        column2: Math.floor(Math.random() * 1000),
        column3: Math.random() > 0.5 ? 'Active' : 'Inactive'
      }))
    }
  }

  // Learning and Statistics
  const recordSuccessfulQuery = async (queryData) => {
    return await apiCall('/learning/record', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  const getLearningStats = async (workspaceId) => {
    const params = workspaceId ? `?workspace_id=${workspaceId}` : ''
    return await apiCall(`/learning/stats${params}`)
  }

  // Query History (mock implementation)
  const getRecentQueries = async (limit = 10) => {
    // In a real app, this would come from your backend
    const mockQueries = [
      {
        id: 1,
        sql: "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'",
        timestamp: '2 minutes ago',
        workspace: 'analytics'
      },
      {
        id: 2,
        sql: "SELECT name, email FROM users ORDER BY created_at DESC LIMIT 100",
        timestamp: '15 minutes ago',
        workspace: 'analytics'
      },
      {
        id: 3,
        sql: "SELECT u.name, COUNT(o.id) as orders FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id",
        timestamp: '1 hour ago',
        workspace: 'analytics'
      },
      {
        id: 4,
        sql: "SELECT status, AVG(amount) FROM orders GROUP BY status",
        timestamp: '2 hours ago',
        workspace: 'sales'
      }
    ]

    return mockQueries.slice(0, limit)
  }

  const saveQuery = async (queryData) => {
    // Mock implementation
    console.log('Saving query:', queryData)
    return { success: true, id: Date.now() }
  }

  const getBookmarkedQueries = async () => {
    // Mock implementation
    return [
      {
        id: 'bookmark1',
        name: 'Daily Active Users',
        sql: "SELECT DATE(created_at) as date, COUNT(DISTINCT user_id) as dau FROM user_sessions WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at)",
        tags: ['daily', 'users', 'analytics']
      }
    ]
  }

  // Schema Information
  const getSchemaInfo = async (workspaceId) => {
    // Mock schema data - replace with real schema introspection
    return {
      tables: [
        {
          name: 'users',
          type: 'table',
          rowCount: 1234567,
          columns: [
            { name: 'id', type: 'INTEGER', nullable: false, primaryKey: true },
            { name: 'name', type: 'VARCHAR(255)', nullable: false },
            { name: 'email', type: 'VARCHAR(255)', nullable: false, unique: true },
            { name: 'created_at', type: 'TIMESTAMP', nullable: false },
            { name: 'updated_at', type: 'TIMESTAMP', nullable: true }
          ],
          indexes: [
            { name: 'users_email_idx', columns: ['email'], unique: true },
            { name: 'users_created_at_idx', columns: ['created_at'] }
          ]
        },
        {
          name: 'orders',
          type: 'table',
          rowCount: 5678901,
          columns: [
            { name: 'id', type: 'INTEGER', nullable: false, primaryKey: true },
            { name: 'user_id', type: 'INTEGER', nullable: false },
            { name: 'amount', type: 'DECIMAL(10,2)', nullable: false },
            { name: 'status', type: 'VARCHAR(50)', nullable: false },
            { name: 'created_at', type: 'TIMESTAMP', nullable: false }
          ],
          indexes: [
            { name: 'orders_user_id_idx', columns: ['user_id'] },
            { name: 'orders_status_idx', columns: ['status'] },
            { name: 'orders_created_at_idx', columns: ['created_at'] }
          ],
          foreignKeys: [
            { column: 'user_id', references: 'users.id' }
          ]
        },
        {
          name: 'products',
          type: 'table',
          rowCount: 45000,
          columns: [
            { name: 'id', type: 'INTEGER', nullable: false, primaryKey: true },
            { name: 'name', type: 'VARCHAR(255)', nullable: false },
            { name: 'price', type: 'DECIMAL(10,2)', nullable: false },
            { name: 'category_id', type: 'INTEGER', nullable: true },
            { name: 'created_at', type: 'TIMESTAMP', nullable: false }
          ]
        },
        {
          name: 'categories',
          type: 'table',
          rowCount: 150,
          columns: [
            { name: 'id', type: 'INTEGER', nullable: false, primaryKey: true },
            { name: 'name', type: 'VARCHAR(100)', nullable: false },
            { name: 'parent_id', type: 'INTEGER', nullable: true }
          ]
        }
      ],
      views: [
        {
          name: 'user_order_summary',
          type: 'view',
          definition: 'SELECT u.id, u.name, COUNT(o.id) as total_orders, SUM(o.amount) as total_spent FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name'
        }
      ]
    }
  }

  // Workspace Management
  const getWorkspaces = async (tenantId) => {
    return await apiCall(`/workspaces?tenant_id=${tenantId}`)
  }

  const createWorkspace = async (workspaceData) => {
    return await apiCall('/workspaces', {
      method: 'POST',
      body: JSON.stringify(workspaceData)
    })
  }

  // Export functionality
  const exportResults = async (results, format = 'csv') => {
    if (format === 'csv') {
      const csv = convertToCSV(results)
      downloadFile(csv, 'query_results.csv', 'text/csv')
    } else if (format === 'json') {
      const json = JSON.stringify(results, null, 2)
      downloadFile(json, 'query_results.json', 'application/json')
    }
  }

  const convertToCSV = (results) => {
    if (!results.data || !results.columns) return ''

    const headers = results.columns.join(',')
    const rows = results.data.map(row =>
      results.columns.map(col => {
        const value = row[col]
        if (value === null || value === undefined) return ''
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return String(value)
      }).join(',')
    )

    return [headers, ...rows].join('\n')
  }

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return {
    // State
    isLoading,
    error,

    // SQL Operations
    analyzeSQL,
    executeSQL,

    // Learning & Stats
    recordSuccessfulQuery,
    getLearningStats,

    // Query Management
    getRecentQueries,
    saveQuery,
    getBookmarkedQueries,

    // Schema
    getSchemaInfo,

    // Workspace
    getWorkspaces,
    createWorkspace,

    // Export
    exportResults
  }
}