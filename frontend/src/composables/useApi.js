import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add workspace header if available
    const workspaceId = localStorage.getItem('l0l1_workspace_id')
    if (workspaceId) {
      config.headers['X-Workspace-ID'] = workspaceId
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api

// SQL Analysis endpoints
export const sqlApi = {
  validate: (query, schema = null) =>
    api.post('/sql/validate', { query, schema }),

  explain: (query) =>
    api.post('/sql/explain', { query }),

  complete: (partialQuery, context = null) =>
    api.post('/sql/complete', { query: partialQuery, context }),

  correct: (query, errorMessage = null) =>
    api.post('/sql/correct', { query, error_message: errorMessage }),

  checkPii: (query) =>
    api.post('/sql/check-pii', { query })
}

// Workspace endpoints
export const workspaceApi = {
  list: () => api.get('/workspaces'),

  get: (id) => api.get(`/workspaces/${id}`),

  create: (data) => api.post('/workspaces', data),

  update: (id, data) => api.put(`/workspaces/${id}`, data),

  delete: (id) => api.delete(`/workspaces/${id}`)
}

// Learning endpoints
export const learningApi = {
  getStats: () => api.get('/learning/stats'),

  record: (query, metadata = {}) =>
    api.post('/learning/record', { query, ...metadata }),

  // Pattern management
  listPatterns: (params = {}) =>
    api.get('/learning/patterns', { params }),

  getPattern: (id) =>
    api.get(`/learning/patterns/${id}`),

  updatePattern: (id, data) =>
    api.put(`/learning/patterns/${id}`, data),

  deletePattern: (id) =>
    api.delete(`/learning/patterns/${id}`),

  bulkDeletePatterns: (data) =>
    api.post('/learning/patterns/bulk-delete', data),

  adjustConfidence: (id, adjustment) =>
    api.post(`/learning/patterns/${id}/confidence`, { adjustment }),

  exportPatterns: (workspaceId = null) =>
    api.get('/learning/export', { params: { workspace_id: workspaceId } }),

  importPatterns: (data, workspaceId, overwrite = false) =>
    api.post('/learning/import', { data, workspace_id: workspaceId, overwrite })
}

// Database connection endpoints
export const databaseApi = {
  getSupported: () =>
    api.get('/databases/supported'),

  list: (workspaceId = null) =>
    api.get('/databases', { params: { workspace_id: workspaceId } }),

  get: (id) =>
    api.get(`/databases/${id}`),

  create: (data) =>
    api.post('/databases', data),

  update: (id, data) =>
    api.put(`/databases/${id}`, data),

  delete: (id) =>
    api.delete(`/databases/${id}`),

  test: (id) =>
    api.post(`/databases/${id}/test`),

  introspectSchema: (id) =>
    api.get(`/databases/${id}/schema`),

  executeQuery: (id, query, params = null, limit = 100) =>
    api.post(`/databases/${id}/query`, { query, params, limit })
}

// Schema management endpoints
export const schemaApi = {
  list: (workspaceId, limit = 20, offset = 0) =>
    api.get('/schemas', { params: { workspace_id: workspaceId, limit, offset } }),

  get: (id) =>
    api.get(`/schemas/${id}`),

  getActive: (workspaceId) =>
    api.get(`/schemas/active/${workspaceId}`),

  create: (data) =>
    api.post('/schemas', data),

  activate: (versionId, workspaceId) =>
    api.post(`/schemas/${versionId}/activate`, null, { params: { workspace_id: workspaceId } }),

  compare: (versionId1, versionId2) =>
    api.post('/schemas/compare', null, { params: { version_id_1: versionId1, version_id_2: versionId2 } }),

  generateMigration: (fromVersionId, toVersionId) =>
    api.post('/schemas/migrate', null, { params: { from_version_id: fromVersionId, to_version_id: toVersionId } }),

  validate: (schemaData) =>
    api.post('/schemas/validate', schemaData),

  export: (versionId, format = 'json') =>
    api.get(`/schemas/${versionId}/export`, { params: { format } }),

  import: (sql, workspaceId) =>
    api.post('/schemas/import', { sql, workspace_id: workspaceId })
}
