import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Eye, Trash2, Lock, Users } from 'lucide-react'
import { jobsAPI, candidatesAPI } from '../../services/api'
import toast from 'react-hot-toast'

const statusBadge = (s) => ({
  active: 'badge-green', closed: 'badge-red', draft: 'badge-gray',
}[s] || 'badge-gray')

export default function MyJobsPage() {
  const [jobs, setJobs]       = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    jobsAPI.myOffers().then((r) => setJobs(r.data.results || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleClose = async (job) => {
    if (!confirm(`Clôturer l'offre "${job.title}" ?`)) return
    try {
      await jobsAPI.close(job.id)
      setJobs((prev) => prev.map((j) => j.id === job.id ? { ...j, status: 'closed' } : j))
      toast.success('Offre clôturée.')
    } catch { toast.error('Erreur lors de la clôture.') }
  }

  const handleDelete = async (job) => {
    if (!confirm(`Supprimer définitivement "${job.title}" ?`)) return
    try {
      await jobsAPI.delete(job.id)
      setJobs((prev) => prev.filter((j) => j.id !== job.id))
      toast.success('Offre supprimée.')
    } catch { toast.error('Erreur lors de la suppression.') }
  }

  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mes offres</h1>
          <p className="text-gray-500 text-sm mt-1">{jobs.length} offre{jobs.length !== 1 ? 's' : ''}</p>
        </div>
        <Link to="/jobs/create" className="btn btn-primary">
          <Plus size={14} /> Nouvelle offre
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p>Vous n'avez pas encore publié d'offre.</p>
          <Link to="/jobs/create" className="btn btn-primary mt-3 inline-flex">Créer une offre</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="card flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
                  <span className={statusBadge(job.status)}>{job.status}</span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {job.location} · {job.contract_type} · Publié le {new Date(job.created_at).toLocaleDateString('fr-FR')}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/dashboard/jobs/${job.id}/applications`}
                  className="btn btn-secondary btn-sm"
                  title="Voir les candidatures"
                >
                  <Users size={13} /> Candidatures
                </Link>
                <Link to={`/jobs/${job.id}`} className="btn btn-ghost btn-sm" title="Voir l'offre">
                  <Eye size={13} />
                </Link>
                {job.status === 'active' && (
                  <button onClick={() => handleClose(job)} className="btn btn-ghost btn-sm text-orange-600" title="Clôturer">
                    <Lock size={13} />
                  </button>
                )}
                <button onClick={() => handleDelete(job)} className="btn btn-ghost btn-sm text-red-500" title="Supprimer">
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
