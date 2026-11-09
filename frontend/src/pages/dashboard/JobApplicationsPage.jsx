import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, ChevronDown, Download } from 'lucide-react'
import { candidatesAPI, jobsAPI, aiAPI } from '../../services/api'
import toast from 'react-hot-toast'

const STATUS_OPTIONS = [
  { value: 'received',    label: 'Reçue' },
  { value: 'analyzing',   label: 'Analyse IA' },
  { value: 'reviewed',    label: 'Examinée' },
  { value: 'shortlisted', label: 'Présélectionnée' },
  { value: 'accepted',    label: 'Acceptée' },
  { value: 'rejected',    label: 'Refusée' },
]

const STATUS_BADGE = {
  received: 'badge-gray', analyzing: 'badge-yellow', reviewed: 'badge-blue',
  shortlisted: 'badge-purple', accepted: 'badge-green', rejected: 'badge-red',
}

function ScoreRing({ score }) {
  if (score == null) return (
    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-xs text-gray-400">
      —
    </div>
  )
  const color = score >= 70 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  return (
    <div
      className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold text-white"
      style={{ background: color }}
    >
      {score}
    </div>
  )
}

export default function JobApplicationsPage() {
  const { jobId } = useParams()
  const [apps, setApps]     = useState([])
  const [job, setJob]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    Promise.all([
      jobsAPI.detail(jobId),
      candidatesAPI.jobApplications(jobId, { ordering: '-compatibility_score' }),
    ]).then(([jobRes, appsRes]) => {
      setJob(jobRes.data)
      setApps(appsRes.data.results || [])
    }).catch(() => toast.error('Erreur de chargement.'))
    .finally(() => setLoading(false))
  }, [jobId])

  const handleStatusChange = async (appId, newStatus) => {
    try {
      const res = await candidatesAPI.updateStatus(appId, { status: newStatus })
      setApps((prev) => prev.map((a) => a.id === appId ? { ...a, status: res.data.status, status_display: res.data.status_display } : a))
      toast.success('Statut mis à jour.')
    } catch { toast.error('Erreur lors de la mise à jour.') }
  }

  const handleRerank = async () => {
    try {
      await aiAPI.rerank(jobId)
      const res = await candidatesAPI.jobApplications(jobId, { ordering: '-compatibility_score' })
      setApps(res.data.results || [])
      toast.success('Candidatures reclassées.')
    } catch { toast.error('Erreur lors du reclassement.') }
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/dashboard" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Retour au tableau de bord
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{job?.title}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {apps.length} candidature{apps.length !== 1 ? 's' : ''} · classées par score IA
          </p>
        </div>
        <button onClick={handleRerank} className="btn btn-secondary btn-sm">
          Reclasser l'IA
        </button>
      </div>

      {apps.length === 0 ? (
        <div className="text-center py-20 text-gray-400">Aucune candidature pour cette offre.</div>
      ) : (
        <div className="space-y-3">
          {apps.map((app, index) => (
            <div key={app.id} className="card">
              <div className="flex items-center gap-4">
                {/* Rang */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${index === 0 ? 'bg-yellow-400 text-white' : index === 1 ? 'bg-gray-300 text-gray-700' : index === 2 ? 'bg-orange-300 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  {index + 1}
                </div>

                {/* Score */}
                <ScoreRing score={app.compatibility_score} />

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-gray-900">{app.candidate_name}</span>
                    <span className={STATUS_BADGE[app.status] || 'badge-gray'}>{app.status_display}</span>
                  </div>
                  <p className="text-xs text-gray-400">{app.candidate_email}</p>
                  {app.matched_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {app.matched_skills.slice(0, 4).map((s) => (
                        <span key={s} className="badge badge-green text-xs">{s}</span>
                      ))}
                      {app.missing_skills?.slice(0, 2).map((s) => (
                        <span key={s} className="badge badge-red text-xs">{s}</span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0">
                  <select
                    className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-600 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                    value={app.status}
                    onChange={(e) => handleStatusChange(app.id, e.target.value)}
                  >
                    {STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>

                  <button
                    onClick={() => setExpanded(expanded === app.id ? null : app.id)}
                    className="btn btn-ghost btn-sm"
                  >
                    <ChevronDown
                      size={14}
                      className={`transition-transform ${expanded === app.id ? 'rotate-180' : ''}`}
                    />
                  </button>
                </div>
              </div>

              {/* Résumé IA expandable */}
              {expanded === app.id && app.ai_summary && (
                <div className="mt-4 border-t border-gray-50 pt-4">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Résumé IA</h4>
                  <p className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">{app.ai_summary}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
