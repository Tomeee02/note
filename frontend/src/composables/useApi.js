// src/composables/useApi.js
import axios from 'axios'

export function useApi(baseURL = 'http://127.0.0.1:8000/api') {
  // Ha egyszerre több kérésre is használod, beállíthatsz itt egy common axios-példányt:
  const api = axios.create({ baseURL })

  const fetchResource = async (endpoint) => {
    const res = await api.get(endpoint)
    return res.data
  }

  const updateResource = async (endpoint, payload) => {
    const res = await api.patch(endpoint, payload)
    return res.data
  }

  const deleteResource = async (endpoint) => {
    const res = await api.delete(endpoint)
    return res.data
  }

  // opcionálisan POST, PUT, stb.
  const createResource = async (endpoint, payload) => {
    const res = await api.post(endpoint, payload)
    return res.data
  }

  return {
    fetchResource,
    updateResource,
    deleteResource,
    createResource,
  }
}
