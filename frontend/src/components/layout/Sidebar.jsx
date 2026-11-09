import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Briefcase, FileText, Send,
  User, MessageSquare, Plus, List,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const navLinkClass = ({ isActive }) =>
  `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
    isActive
      ? 'bg-primary-50 text-primary-700 font-semibold'
      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
  }`

export default function Sidebar() {
  const { isCandidat, isRecruteur, isAdmin } = useAuth()

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-gray-100 overflow-y-auto pt-4 pb-8">
      <nav className="px-3 space-y-0.5">

        {/* ── Commun ── */}
        <div className="px-3 py-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Menu</p>
        </div>

        <NavLink to="/jobs" className={navLinkClass}>
          <Briefcase size={16} /> Offres d'emploi
        </NavLink>

        <NavLink to="/chatbot" className={navLinkClass}>
          <MessageSquare size={16} /> Chatbot RH
        </NavLink>

        {/* ── Candidat ── */}
        {isCandidat && (
          <>
            <div className="px-3 py-2 mt-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Candidat</p>
            </div>
            <NavLink to="/my-cvs" className={navLinkClass}>
              <FileText size={16} /> Mes CV
            </NavLink>
            <NavLink to="/my-applications" className={navLinkClass}>
              <Send size={16} /> Mes candidatures
            </NavLink>
            <NavLink to="/profile" className={navLinkClass}>
              <User size={16} /> Mon profil
            </NavLink>
          </>
        )}

        {/* ── Recruteur / Admin ── */}
        {(isRecruteur || isAdmin) && (
          <>
            <div className="px-3 py-2 mt-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recruteur</p>
            </div>
            <NavLink to="/dashboard" className={navLinkClass}>
              <LayoutDashboard size={16} /> Tableau de bord
            </NavLink>
            <NavLink to="/jobs/my-offers" className={navLinkClass}>
              <List size={16} /> Mes offres
            </NavLink>
            <NavLink to="/jobs/create" className={navLinkClass}>
              <Plus size={16} /> Créer une offre
            </NavLink>
          </>
        )}
      </nav>
    </aside>
  )
}
