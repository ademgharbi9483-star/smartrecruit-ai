import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { Users, Briefcase, TrendingUp, Star, ArrowRight } from 'lucide-react'
import { candidatesAPI } from '../../services/api'
import toast from 'react-hot-toast'

function StatCard({ icon: Icon, label, value, sub, color = 'primary' }) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600',
    green:   'bg-green-50 text-green-600',
    purple:  'bg-purple-50 text-purple-600',
    yellow:  'bg-yellow-50 text-yellow-600',
  }
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${colors[color]}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-600 font-medium">{label}</p>
        {sub && <p className="text-xs text-gray-400">{sub}</p>}
      </div>
    </div>
  )
}

const STATUS_LABEL = {
  received: 'Reçues', analyzing: 'Analyse IA', reviewed: 'Examinées',
  shortlisted: 'Présélectionnées', accepted: 'Acceptées', rejected: 'Refusées',
}

export default function RecruiterDashboard() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    candidatesAPI.dashboard()
      .then((res) => setData(res.data))
      .catch(() => toast.error('Erreur de chargement du tableau de bord.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )

  if (!data) return null

  const { global: g, by_status, jobs_summary, top_applications } = data

  // Données pour le graphique
  const chartData = Object.entries(by_status).map(([key, val]) => ({
    name: STATUS_LABEL[key] || key,
    count: val.count,
  }))

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-500 text-sm mt-1">Vue synthétique de votre activité de recrutement.</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Briefcase}   label="Offres publiées"  value={g.total_jobs}        sub={`${g.active_jobs} actives`}     color="primary" />
        <StatCard icon={Users}       label="Candidatures"     value={g.total_applications} sub="toutes offres confondues"       color="green" />
        <StatCard icon={TrendingUp}  label="Score moyen IA"   value={`${g.avg_compatibility_score}/100`}   sub="compatibilité moyenne" color="purple" />
        <StatCard icon={Star}        label="Top score"        value={top_applications?.[0]?.compatibility_score ? `${top_applications[0].compatibility_score}/100` : 'N/A'} sub="meilleur profil" color="yellow" />
      </div>

      {/* Graphique + Top candidatures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Répartition par statut */}
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">Répartition par statut</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top candidats */}
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">Top candidats</h2>
          {top_applications?.length === 0
            ? <p className="text-gray-400 text-sm">Aucun candidat scoré pour l'instant.</p>
            : (
              <div className="space-y-3">
                {top_applications?.slice(0, 5).map((app, i) => (
                  <div key={app.id} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i === 0 ? 'bg-yellow-400 text-white' : 'bg-gray-100 text-gray-500'}`}>
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{app.candidate_name}</p>
                      <p className="text-xs text-gray-400 truncate">{app.job_title}</p>
                    </div>
                    <span className={`badge text-xs font-bold ${app.compatibility_score >= 70 ? 'badge-green' : app.compatibility_score >= 50 ? 'badge-yellow' : 'badge-red'}`}>
                      {app.compatibility_score}/100
                    </span>
                  </div>
                ))}
              </div>
            )
          }
        </div>
      </div>

      {/* Offres & candidatures */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Mes offres</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Offre</th>
                <th className="text-center py-2 px-3 text-gray-400 font-medium">Statut</th>
                <th className="text-center py-2 px-3 text-gray-400 font-medium">Candidatures</th>
                <th className="text-center py-2 px-3 text-gray-400 font-medium">Score moy.</th>
                <th className="py-2 px-3"></th>
              </tr>
            </thead>
            <tbody>
              {jobs_summary.map((job) => (
                <tr key={job.job_id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="py-2.5 px-3 font-medium text-gray-900 max-w-[200px] truncate">{job.title}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`badge ${job.status === 'active' ? 'badge-green' : 'badge-gray'}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center font-medium">{job.applications}</td>
                  <td className="py-2.5 px-3 text-center">
                    {job.avg_score > 0 ? (
                      <span className={`font-bold ${job.avg_score >= 70 ? 'text-green-600' : job.avg_score >= 50 ? 'text-yellow-600' : 'text-red-500'}`}>
                        {job.avg_score}
                      </span>
                    ) : '—'}
                  </td>
                  <td className="py-2.5 px-3">
                    <Link
                      to={`/dashboard/jobs/${job.job_id}/applications`}
                      className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-xs font-medium"
                    >
                      Voir <ArrowRight size={11} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {jobs_summary.length === 0 && (
            <p className="text-center text-gray-400 py-6 text-sm">Aucune offre publiée.</p>
          )}
        </div>
      </div>
    </div>
  )
}
