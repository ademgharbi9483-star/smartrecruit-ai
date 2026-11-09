import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Send, ChevronRight } from 'lucide-react'
import { candidatesAPI } from '../../services/api'
import toast from 'react-hot-toast'

const STATUS_BADGE = {
  received:   'badge-gray',
  analyzing:  'badge-yellow',
  reviewed:   'badge-blue',
  shortlisted:'badge-purple',
  accepted:   'badge-green',
  rejected:   'badge-red',
}

const STATUS_LABEL = {
  received:    'Reçue',
  analyzing:   'Analyse IA',
  reviewed:    'Examinée',
  shortlisted: 'Présélectionnée',
  accepted:    'Acceptée',
  rejected:    'Refusée',
}

function ScoreBadge({ score }) {
  if (score == null) return <span className="badge badge-gray">Calcul en cours</span>
  const color = score >= 70 ? 'text-green-700 bg-green-50' : score >= 50 ? 'text-yellow-700 bg-yellow-50' : 'text-red-700 bg-red-50'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${color}`}>
      {score}/100
    </span>
  )
}

export default function MyApplicationsPage() {
  const [apps, setApps]       = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    candidatesAPI.myApplications()
      .then((res) => setApps(res.data.results || []))
      .catch(() => toast.error('Erreur lors du chargement.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Mes candidatures</h1>
        <p className="text-gray-500 text-sm mt-1">{apps.length} candidature{apps.length !== 1 ? 's' : ''}</p>
      </div>

      {apps.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Send size={40} className="mx-auto mb-3 opacity-30" />
          <p>Vous n'avez pas encore postulé à une offre.</p>
          <Link to="/jobs" className="btn btn-primary mt-3 inline-flex">Explorer les offres</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map((app) => (
            <div key={app.id} className="card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold text-gray-900">{app.job_title}</h3>
                    <span className={STATUS_BADGE[app.status] || 'badge-gray'}>
                      {STATUS_LABEL[app.status] || app.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Postulé le {new Date(app.applied_at).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <ScoreBadge score={app.compatibility_score} />
              </div>

              {app.ai_summary && (
                <p className="text-xs text-gray-500 mt-3 border-t border-gray-50 pt-3 line-clamp-2">
                  {app.ai_summary.split('\n')[0]}
                </p>
              )}

              {(app.matched_skills?.length > 0 || app.missing_skills?.length > 0) && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {app.matched_skills?.slice(0, 4).map((s) => (
                    <span key={s} className="badge badge-green">{s}</span>
                  ))}
                  {app.missing_skills?.slice(0, 3).map((s) => (
                    <span key={s} className="badge badge-red">{s}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
