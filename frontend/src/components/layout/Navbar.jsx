import { Link, useNavigate } from 'react-router-dom'
import { LogOut, Bell, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [dropOpen, setDropOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    toast.success('Déconnexion réussie')
    navigate('/login')
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 h-16 px-6 flex items-center justify-between shadow-sm">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2 font-bold text-lg text-primary-700">
        <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white font-black text-xs">
          SR
        </div>
        <span className="hidden sm:block">SmartRecruit AI</span>
      </Link>

      {/* Navigation publique */}
      <div className="flex items-center gap-1 text-sm text-gray-600">
        <Link to="/jobs" className="px-3 py-1.5 rounded-md hover:bg-gray-100 transition-colors">
          Offres
        </Link>
        {!isAuthenticated && (
          <>
            <Link to="/login"    className="btn btn-ghost btn-sm">Connexion</Link>
            <Link to="/register" className="btn btn-primary btn-sm">S'inscrire</Link>
          </>
        )}
      </div>

      {/* Zone utilisateur connecté */}
      {isAuthenticated && (
        <div className="flex items-center gap-3">
          <button className="relative p-2 rounded-full hover:bg-gray-100 text-gray-500">
            <Bell size={18} />
          </button>

          <div className="relative">
            <button
              onClick={() => setDropOpen((v) => !v)}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-bold">
                {user?.full_name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-gray-800 leading-tight">
                  {user?.full_name || 'Utilisateur'}
                </p>
                <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
              </div>
              <ChevronDown size={14} className="text-gray-400" />
            </button>

            {dropOpen && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut size={14} />
                  Déconnexion
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
