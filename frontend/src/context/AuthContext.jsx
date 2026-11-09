/**
 * SmartRecruit AI — Contexte d'authentification.
 * Gère l'état global de l'utilisateur connecté, les tokens JWT
 * et expose les fonctions login / logout.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // ── Initialisation : restaurer la session depuis localStorage ────────────────
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      authAPI.me()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  // ── Connexion ──────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const res = await authAPI.login({ email, password })
    const { access, refresh, user: userData } = res.data
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    setUser(userData)
    return userData
  }, [])

  // ── Déconnexion ──────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await authAPI.logout(refresh)
    } catch (_) { /* ignore */ }
    localStorage.clear()
    setUser(null)
  }, [])

  // ── Mise à jour du profil ───────────────────────────────────────────────────
  const updateUser = useCallback((updates) => {
    setUser((prev) => ({ ...prev, ...updates }))
  }, [])

  const isCandidat  = user?.role === 'candidat'
  const isRecruteur = user?.role === 'recruteur'
  const isAdmin     = user?.role === 'admin'

  return (
    <AuthContext.Provider value={{
      user, loading,
      login, logout, updateUser,
      isAuthenticated: !!user,
      isCandidat, isRecruteur, isAdmin,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans AuthProvider')
  return ctx
}
