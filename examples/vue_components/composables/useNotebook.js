import { ref } from 'vue'

const API_BASE = '/api' // Adjust this to match your API base URL

export function useNotebook() {
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
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // Session Management
  const createSession = async (sessionData) => {
    return await apiCall('/ui/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData)
    })
  }

  const getSession = async (sessionId) => {
    return await apiCall(`/ui/sessions/${sessionId}`)
  }

  const updateSession = async (sessionId, sessionData) => {
    return await apiCall(`/ui/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData)
    })
  }

  const deleteSession = async (sessionId) => {
    return await apiCall(`/ui/sessions/${sessionId}`, {
      method: 'DELETE'
    })
  }

  const listSessions = async (filters = {}) => {
    const params = new URLSearchParams(filters)
    return await apiCall(`/ui/sessions?${params}`)
  }

  // Cell Management
  const createCell = async (sessionId, cellData) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells`, {
      method: 'POST',
      body: JSON.stringify(cellData)
    })
  }

  const getCell = async (sessionId, cellId) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells/${cellId}`)
  }

  const updateCell = async (sessionId, cellId, cellData) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells/${cellId}`, {
      method: 'PUT',
      body: JSON.stringify(cellData)
    })
  }

  const deleteCell = async (sessionId, cellId) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells/${cellId}`, {
      method: 'DELETE'
    })
  }

  const moveCell = async (sessionId, cellId, moveData) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells/${cellId}/move`, {
      method: 'PUT',
      body: JSON.stringify(moveData)
    })
  }

  const executeCell = async (sessionId, cellId, executionData) => {
    return await apiCall(`/ui/sessions/${sessionId}/cells/${cellId}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        cell_id: cellId,
        ...executionData
      })
    })
  }

  // Notebook Operations
  const clearAllOutputs = async (sessionId) => {
    return await apiCall(`/ui/sessions/${sessionId}/outputs`, {
      method: 'DELETE'
    })
  }

  const exportNotebook = async (sessionId) => {
    return await apiCall(`/ui/sessions/${sessionId}/export`)
  }

  const importNotebook = async (sessionId, notebookData) => {
    return await apiCall(`/ui/sessions/${sessionId}/import`, {
      method: 'POST',
      body: JSON.stringify(notebookData)
    })
  }

  // SQL Analysis
  const validateQuery = async (queryData) => {
    return await apiCall('/sql/validate', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  const explainQuery = async (queryData) => {
    return await apiCall('/sql/explain', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  const completeQuery = async (queryData) => {
    return await apiCall('/sql/complete', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  const correctQuery = async (queryData) => {
    return await apiCall('/sql/correct', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  const checkPII = async (queryData) => {
    return await apiCall('/sql/check-pii', {
      method: 'POST',
      body: JSON.stringify(queryData)
    })
  }

  // Learning
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

  // Workspace Management
  const listWorkspaces = async (tenantId) => {
    return await apiCall(`/workspaces?tenant_id=${tenantId}`)
  }

  const createWorkspace = async (workspaceData) => {
    return await apiCall('/workspaces', {
      method: 'POST',
      body: JSON.stringify(workspaceData)
    })
  }

  const getWorkspace = async (workspaceId) => {
    return await apiCall(`/workspaces/${workspaceId}`)
  }

  const updateWorkspace = async (workspaceId, workspaceData) => {
    return await apiCall(`/workspaces/${workspaceId}`, {
      method: 'PUT',
      body: JSON.stringify(workspaceData)
    })
  }

  const deleteWorkspace = async (workspaceId) => {
    return await apiCall(`/workspaces/${workspaceId}`, {
      method: 'DELETE'
    })
  }

  // UI Helpers
  const renderAnalysisResults = async (analysisData, format = 'vue') => {
    return await apiCall('/ui/render', {
      method: 'POST',
      body: JSON.stringify({
        analysis_results: analysisData,
        format
      })
    })
  }

  const getCellTemplate = async (cellType = 'sql') => {
    return await apiCall(`/ui/templates/cell?cell_type=${cellType}`)
  }

  const getNotebookTemplate = async (workspaceId, title = 'New Notebook') => {
    return await apiCall(`/ui/templates/notebook?workspace_id=${workspaceId}&title=${encodeURIComponent(title)}`)
  }

  const getToolbarConfig = async () => {
    return await apiCall('/ui/toolbar')
  }

  // Health Check
  const checkHealth = async () => {
    return await apiCall('/health')
  }

  return {
    // State
    isLoading,
    error,

    // Session Management
    createSession,
    getSession,
    updateSession,
    deleteSession,
    listSessions,

    // Cell Management
    createCell,
    getCell,
    updateCell,
    deleteCell,
    moveCell,
    executeCell,

    // Notebook Operations
    clearAllOutputs,
    exportNotebook,
    importNotebook,

    // SQL Analysis
    validateQuery,
    explainQuery,
    completeQuery,
    correctQuery,
    checkPII,

    // Learning
    recordSuccessfulQuery,
    getLearningStats,

    // Workspace Management
    listWorkspaces,
    createWorkspace,
    getWorkspace,
    updateWorkspace,
    deleteWorkspace,

    // UI Helpers
    renderAnalysisResults,
    getCellTemplate,
    getNotebookTemplate,
    getToolbarConfig,

    // Health
    checkHealth
  }
}