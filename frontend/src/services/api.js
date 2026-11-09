/**
 * SmartRecruit AI — Client API Axios
 * Gère l'authentification JWT, le refresh automatique des tokens
 * et les intercepteurs de requêtes/réponses.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// ── Intercepteur de requête : injection du token ──────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Intercepteur de réponse : refresh token si 401 ───────────────────────────
let _isRefreshing = false
let _waitQueue = []

const processQueue = (error, token = null) => {
  _waitQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)))
  _waitQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      if (_isRefreshing) {
        return new Promise((resolve, reject) => {
          _waitQueue.push({ resolve, reject })
        })
          .then((token) => {
            original.headers.Authorization = `Bearer ${token}`
            return api(original)
          })
          .catch((err) => Promise.reject(err))
      }

      original._retry = true
      _isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        _isRefreshing = false
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const res = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })
        const newAccess = res.data.access
        localStorage.setItem('access_token', newAccess)
        api.defaults.headers.common.Authorization = `Bearer ${newAccess}`
        processQueue(null, newAccess)
        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)
      } catch (refreshError) {
        processQueue(refreshError, null)
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        _isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// ── Services Auth ─────────────────────────────────────────────────────────────
export const authAPI = {
  register:  (data) => api.post('/auth/register/', data),
  login:     (data) => api.post('/auth/login/', data),
  logout:    (refreshToken) => api.post('/auth/logout/', { refresh_token: refreshToken }),
  me:        () => api.get('/auth/me/'),
  updateProfile: (data) => api.patch('/auth/profile/', data),
  changePassword: (data) => api.put('/auth/change-password/', data),
  resetPassword:  (email) => api.post('/auth/password-reset/', { email }),
}

// ── Services Jobs ─────────────────────────────────────────────────────────────
export const jobsAPI = {
  list:       (params) => api.get('/jobs/', { params }),
  detail:     (id) => api.get(`/jobs/${id}/`),
  create:     (data) => api.post('/jobs/create/', data),
  update:     (id, data) => api.patch(`/jobs/${id}/update/`, data),
  delete:     (id) => api.delete(`/jobs/${id}/delete/`),
  close:      (id) => api.post(`/jobs/${id}/close/`),
  myOffers:   (params) => api.get('/jobs/my-offers/', { params }),
  stats:      () => api.get('/jobs/stats/'),
}

// ── Services Candidatures ─────────────────────────────────────────────────────
export const candidatesAPI = {
  getProfile:    () => api.get('/candidates/profile/'),
  updateProfile: (data) => api.patch('/candidates/profile/', data),

  uploadCV:    (formData) => api.post('/candidates/cvs/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  listCVs:       () => api.get('/candidates/cvs/'),
  deleteCV:      (id) => api.delete(`/candidates/cvs/${id}/`),
  reanalyzeCV:   (id) => api.post(`/candidates/cvs/${id}/reanalyze/`),

  apply:         (data) => api.post('/candidates/applications/', data),
  myApplications: (params) => api.get('/candidates/applications/mine/', { params }),
  applicationDetail: (id) => api.get(`/candidates/applications/${id}/`),

  jobApplications: (jobId, params) =>
    api.get(`/candidates/jobs/${jobId}/applications/`, { params }),
  updateStatus: (appId, data) =>
    api.patch(`/candidates/applications/${appId}/status/`, data),

  dashboard: () => api.get('/candidates/dashboard/'),
}

// ── Services IA ───────────────────────────────────────────────────────────────
export const aiAPI = {
  chatbot:        (message, conversationId) =>
    api.post('/ai/chatbot/', { message, conversation_id: conversationId }),
  analyzeCV:      (cvId) => api.post(`/ai/analyze-cv/${cvId}/`),
  cvResult:       (cvId) => api.get(`/ai/cv/${cvId}/result/`),
  aiDashboard:    () => api.get('/ai/dashboard/'),
  rerank:         (jobId) => api.post(`/ai/rerank/${jobId}/`),
}

export default api
