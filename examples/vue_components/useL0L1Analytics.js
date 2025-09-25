/**
 * Vue Composable for l0l1 Analytics Integration
 *
 * Provides reactive interface to l0l1 API endpoints for:
 * - SQL analysis and validation
 * - Query execution
 * - Learning insights
 * - Graph-based intelligence
 * - Workspace management
 */

import { ref, reactive, computed } from 'vue'

// API base URL - adjust based on your setup
const API_BASE = import.meta.env.VITE_L0L1_API_URL || 'http://localhost:8000/api'

export function useL0L1Analytics() {
  // State
  const isLoading = ref(false)
  const error = ref(null)
  const currentWorkspace = ref('demo_ecommerce')

  // Request helper
  const apiRequest = async (endpoint, options = {}) => {
    const url = `${API_BASE}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // SQL Analysis
  const analyzeSQL = async (query, options = {}) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiRequest('/sql/analyze', {
        method: 'POST',
        body: JSON.stringify({
          workspace_id: currentWorkspace.value,
          query,
          ...options
        })
      })

      return response
    } catch (err) {
      console.error('SQL analysis failed:', err)

      // Return mock data for demo purposes
      return {
        is_valid: query.trim().toLowerCase().startsWith('select'),
        issues: query.trim().toLowerCase().startsWith('select') ? [] : ['Query must start with SELECT'],
        pii_detected: [],
        performance_hints: [
          'Consider adding LIMIT clause for large result sets',
          'Use indexed columns in WHERE clauses for better performance'
        ],
        suggestions: [
          'SELECT * FROM users LIMIT 100',
          'SELECT name, email FROM users WHERE created_at >= CURRENT_DATE - 30',
          'SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id'
        ]
      }
    } finally {
      isLoading.value = false
    }
  }

  // Execute SQL Query
  const executeSQL = async (query) => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiRequest('/sql/execute', {
        method: 'POST',
        body: JSON.stringify({
          workspace_id: currentWorkspace.value,
          query
        })
      })

      return response
    } catch (err) {
      console.error('SQL execution failed:', err)

      // Return mock data for demo
      return {
        success: true,
        columns: ['id', 'name', 'email', 'created_at'],
        data: [
          { id: 1, name: 'John Doe', email: 'john@demo.com', created_at: '2024-01-15' },
          { id: 2, name: 'Jane Smith', email: 'jane@demo.com', created_at: '2024-01-14' },
          { id: 3, name: 'Mike Johnson', email: 'mike@demo.com', created_at: '2024-01-13' }
        ],
        row_count: 3,
        execution_time: 142
      }
    } finally {
      isLoading.value = false
    }
  }

  // Get Learning Statistics
  const getLearningStats = async (workspaceId = null) => {
    const workspace = workspaceId || currentWorkspace.value

    try {
      const response = await apiRequest(`/workspaces/${workspace}/learning/stats`)
      return response
    } catch (err) {
      console.error('Failed to fetch learning stats:', err)

      // Return mock data
      return {
        total_queries: 234,
        avg_execution_time: 186,
        success_rate: 0.94,
        most_used_tables: {
          'users': 156,
          'orders': 142,
          'products': 89
        },
        performance_distribution: {
          'fast': 145,
          'medium': 67,
          'slow': 22
        }
      }
    }
  }

  // Get Recent Queries
  const getRecentQueries = async (limit = 10) => {
    try {
      const response = await apiRequest(`/workspaces/${currentWorkspace.value}/queries/recent?limit=${limit}`)
      return response.queries || []
    } catch (err) {
      console.error('Failed to fetch recent queries:', err)

      // Return mock data
      return [
        {
          id: 1,
          sql: 'SELECT SUM(total_amount) FROM orders WHERE status = \'delivered\'',
          timestamp: '2024-01-15 14:30:00',
          execution_time: 156,
          user: 'Sarah Johnson'
        },
        {
          id: 2,
          sql: 'SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - 30',
          timestamp: '2024-01-15 10:15:00',
          execution_time: 89,
          user: 'Mike Chen'
        },
        {
          id: 3,
          sql: 'SELECT p.name, SUM(oi.quantity) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name',
          timestamp: '2024-01-14 16:45:00',
          execution_time: 234,
          user: 'Jessica Liu'
        }
      ]
    }
  }

  // Get Workspace Insights
  const getWorkspaceInsights = async (workspaceId = null) => {
    const workspace = workspaceId || currentWorkspace.value

    try {
      const response = await apiRequest(`/workspaces/${workspace}/insights`)
      return response
    } catch (err) {
      console.error('Failed to fetch workspace insights:', err)

      // Return mock data
      return {
        most_used_tables: {
          'users': 156,
          'orders': 142,
          'products': 89,
          'order_items': 78,
          'categories': 34,
          'reviews': 23
        },
        performance_distribution: {
          fast: 145,
          medium: 67,
          slow: 22
        },
        total_queries_analyzed: 234,
        unique_tables: 12,
        complexity_trends: {
          trend: 'increasing',
          avg_complexity: 6.2
        },
        team_activity: {
          'sales': 89,
          'marketing': 67,
          'finance': 45,
          'product': 33
        }
      }
    }
  }

  // Get Graph Intelligence
  const getGraphIntelligence = async (workspaceId = null) => {
    const workspace = workspaceId || currentWorkspace.value

    try {
      const response = await apiRequest(`/workspaces/${workspace}/graph/intelligence`)
      return response
    } catch (err) {
      console.error('Failed to fetch graph intelligence:', err)

      // Return comprehensive mock data for demo
      return {
        workspace_insights: {
          most_used_tables: {
            'users': 156,
            'orders': 142,
            'products': 89,
            'order_items': 78
          },
          performance_distribution: {
            fast: 145,
            medium: 67,
            slow: 22
          },
          total_queries_analyzed: 234,
          unique_tables: 12,
          complexity_trends: {
            trend: 'increasing',
            avg_complexity: 6.2
          }
        },

        table_relationships: [
          {
            id: 1,
            from_table: 'users',
            to_table: 'orders',
            join_pattern: 'users.id = orders.user_id',
            confidence: 0.95,
            frequency: 156,
            avg_performance: '180ms'
          },
          {
            id: 2,
            from_table: 'orders',
            to_table: 'order_items',
            join_pattern: 'orders.id = order_items.order_id',
            confidence: 0.98,
            frequency: 142,
            avg_performance: '145ms'
          },
          {
            id: 3,
            from_table: 'products',
            to_table: 'order_items',
            join_pattern: 'products.id = order_items.product_id',
            confidence: 0.92,
            frequency: 89,
            avg_performance: '167ms'
          }
        ],

        recommended_joins: [
          {
            id: 1,
            sql: 'JOIN orders ON users.id = orders.user_id',
            reason: 'Commonly used with users table (95% confidence)',
            confidence: 0.95
          },
          {
            id: 2,
            sql: 'JOIN order_items ON orders.id = order_items.order_id',
            reason: 'Standard pattern for order details',
            confidence: 0.98
          }
        ],

        performance_insights: [
          {
            id: 1,
            type: 'slow_table',
            title: 'Large table scan on orders',
            description: 'Queries on orders table average 1.2s without date filters',
            suggestion: 'WHERE orders.created_at >= CURRENT_DATE - INTERVAL \'30 days\'',
            suggestion_text: 'Add date filter to reduce scan'
          },
          {
            id: 2,
            type: 'missing_index',
            title: 'Missing index opportunity',
            description: 'created_at column frequently used in WHERE clauses',
            suggestion_text: 'Consider adding index on created_at'
          },
          {
            id: 3,
            type: 'optimization',
            title: 'JOIN performance boost',
            description: 'User-order joins perform 3x better with user_id filters',
            suggestion: 'WHERE users.id IN (SELECT user_id FROM orders WHERE created_at >= \'2024-01-01\')',
            suggestion_text: 'Filter users before joining'
          }
        ],

        optimization_opportunities: [
          {
            id: 1,
            title: 'Add LIMIT clauses',
            description: 'Large result sets detected in similar queries',
            impact: '60% faster execution',
            affected_queries: 12
          },
          {
            id: 2,
            title: 'Use indexed columns for filtering',
            description: 'Non-indexed columns frequently used in WHERE clauses',
            impact: '75% faster execution',
            affected_queries: 8
          }
        ],

        team_patterns: {
          'sales': ['Revenue analysis', 'Customer segmentation', 'Conversion tracking'],
          'marketing': ['Campaign performance', 'Funnel analysis', 'Attribution modeling'],
          'finance': ['Cost analysis', 'Profitability tracking', 'Budget forecasting'],
          'product': ['Feature adoption', 'User engagement', 'Retention analysis']
        },

        popular_templates: [
          {
            id: 1,
            name: 'Monthly Revenue',
            sql: 'SELECT DATE_TRUNC(\'month\', created_at) as month, SUM(total_amount) as revenue FROM orders WHERE status = \'delivered\' GROUP BY 1 ORDER BY 1 DESC',
            usage_count: 47,
            team: 'sales'
          },
          {
            id: 2,
            name: 'Customer Order Summary',
            sql: 'SELECT u.name, COUNT(o.id) as orders, SUM(o.total_amount) as total FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY total DESC',
            usage_count: 32,
            team: 'sales'
          },
          {
            id: 3,
            name: 'Product Performance',
            sql: 'SELECT p.name, SUM(oi.quantity) as units, SUM(oi.total_price) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name ORDER BY revenue DESC',
            usage_count: 28,
            team: 'sales'
          }
        ]
      }
    }
  }

  // Get Query Suggestions
  const getQuerySuggestions = async (partialQuery, context = {}) => {
    try {
      const response = await apiRequest('/sql/suggestions', {
        method: 'POST',
        body: JSON.stringify({
          workspace_id: currentWorkspace.value,
          partial_query: partialQuery,
          context
        })
      })

      return response.suggestions || []
    } catch (err) {
      console.error('Failed to get query suggestions:', err)

      // Return context-aware mock suggestions
      const suggestions = []

      if (partialQuery.toLowerCase().includes('select')) {
        suggestions.push(
          'SELECT * FROM users LIMIT 100',
          'SELECT name, email FROM users WHERE created_at >= CURRENT_DATE - 30',
          'SELECT COUNT(*) FROM users'
        )
      }

      if (partialQuery.toLowerCase().includes('users')) {
        suggestions.push(
          'JOIN orders ON users.id = orders.user_id',
          'WHERE users.created_at >= \'2024-01-01\'',
          'ORDER BY users.created_at DESC'
        )
      }

      return suggestions.slice(0, 5)
    }
  }

  // Format Query
  const formatQuery = async (query) => {
    try {
      const response = await apiRequest('/sql/format', {
        method: 'POST',
        body: JSON.stringify({ query })
      })

      return response.formatted_query || query
    } catch (err) {
      console.error('Failed to format query:', err)

      // Simple local formatting fallback
      return query
        .replace(/\bSELECT\b/gi, 'SELECT')
        .replace(/\bFROM\b/gi, '\nFROM')
        .replace(/\bWHERE\b/gi, '\nWHERE')
        .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
        .replace(/\bORDER BY\b/gi, '\nORDER BY')
        .replace(/\bLIMIT\b/gi, '\nLIMIT')
    }
  }

  // Check PII
  const checkPII = async (query) => {
    try {
      const response = await apiRequest('/sql/check-pii', {
        method: 'POST',
        body: JSON.stringify({
          workspace_id: currentWorkspace.value,
          query
        })
      })

      return response
    } catch (err) {
      console.error('Failed to check PII:', err)

      // Simple mock PII detection
      const piiPatterns = [
        { pattern: /email/i, type: 'EMAIL_ADDRESS' },
        { pattern: /phone/i, type: 'PHONE_NUMBER' },
        { pattern: /ssn/i, type: 'SSN' },
        { pattern: /'[\w.-]+@[\w.-]+\.\w+'/g, type: 'EMAIL_ADDRESS' }
      ]

      const detected = []
      for (const { pattern, type } of piiPatterns) {
        const matches = query.match(pattern)
        if (matches) {
          matches.forEach(match => {
            detected.push({
              entity_type: type,
              text: match,
              confidence: 0.9
            })
          })
        }
      }

      return {
        pii_detected: detected,
        is_safe: detected.length === 0
      }
    }
  }

  // Get Workspace Schema
  const getWorkspaceSchema = async (workspaceId = null) => {
    const workspace = workspaceId || currentWorkspace.value

    try {
      const response = await apiRequest(`/workspaces/${workspace}/schema`)
      return response
    } catch (err) {
      console.error('Failed to fetch workspace schema:', err)

      // Return mock schema
      return {
        tables: [
          {
            name: 'users',
            type: 'table',
            row_count: '12.5K',
            columns: [
              { name: 'id', type: 'INTEGER', nullable: false, primary_key: true },
              { name: 'name', type: 'VARCHAR', nullable: false },
              { name: 'email', type: 'VARCHAR', nullable: false },
              { name: 'created_at', type: 'TIMESTAMP', nullable: false }
            ]
          },
          {
            name: 'orders',
            type: 'table',
            row_count: '58.2K',
            columns: [
              { name: 'id', type: 'INTEGER', nullable: false, primary_key: true },
              { name: 'user_id', type: 'INTEGER', nullable: false },
              { name: 'status', type: 'VARCHAR', nullable: false },
              { name: 'total_amount', type: 'DECIMAL', nullable: false },
              { name: 'created_at', type: 'TIMESTAMP', nullable: false }
            ]
          },
          {
            name: 'products',
            type: 'table',
            row_count: '2.1K',
            columns: [
              { name: 'id', type: 'INTEGER', nullable: false, primary_key: true },
              { name: 'name', type: 'VARCHAR', nullable: false },
              { name: 'price', type: 'DECIMAL', nullable: false },
              { name: 'category_id', type: 'INTEGER', nullable: true }
            ]
          }
        ]
      }
    }
  }

  // Computed values
  const hasError = computed(() => error.value !== null)

  return {
    // State
    isLoading,
    error,
    hasError,
    currentWorkspace,

    // Methods
    analyzeSQL,
    executeSQL,
    getLearningStats,
    getRecentQueries,
    getWorkspaceInsights,
    getGraphIntelligence,
    getQuerySuggestions,
    formatQuery,
    checkPII,
    getWorkspaceSchema
  }
}

// Export for direct usage
export default useL0L1Analytics