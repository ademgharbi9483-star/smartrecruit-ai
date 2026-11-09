import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { MapPin, Briefcase, Clock, CheckCircle, ArrowLeft, Send } from 'lucide-react'
import { jobsAPI, candidatesAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

export default function JobDetailPage() {
  const { id } = useParams()
  const { isCandidat, isAuthenticated } = useAuth()

  const [job, setJob]           = useState(null)
  const [cvs, setCVs]           = useState([])
  const [selectedCV, setSelected] = useState('')
  const [coverLetter, setCover]  = useState('')
  const [applying, setApplying]  = useState(false)
  const [applied, setApplied]    = useState(false)
  const [loading, setLoading]    = useState(true)

  useEffect(() => {
    jobsAPI.detail(id)
      .then((r) => setJob(r.data))
      .catch(() => toast.error('Offre introuvable.'))
      .finally(() => setLoading(false))

    if (isCandidat) {
      candidatesAPI.listCVs().then((r) => {
        setCVs(r.data.results || r.data)
        const primary = (r.data.results || r.data).find((cv) => cv.is_primary)
        if (primary) setSelected(String(primary.id))
      }).catch(() => {})
    }
  }, [id, isCandidat])

  const handleApply = async () => {
    if (!selectedCV) return toast.error('Sélectionnez un CV.')
    setApplying(true)
    try {
      await candidatesAPI.apply({ job_offer: id, cv: selectedCV, cover_letter: coverLetter })
      setApplied(true)
      toast.success('Candidature envoyée ! Notre IA analyse votre profil.')
    } catch (err) {
      const msg = err.response?.data?.job_offer?.[0] || err.response?.data?.detail || 'Erreur lors de la candidature.'
      toast.error(msg)
    } finally {
      setApplying(false)
    }
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )
  if (!job) return <p className="text-center text-gray-500 py-20">Offre introuvable.</p>

  return (
    <div className="max-w-3xl mx-auto">
      <Link to="/jobs" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Retour aux offres
      </Link>

      {/* En-tête */}
      <div className="card mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
              <span className="flex items-center gap-1"><MapPin size={13} /> {job.location}</span>
              <span className="flex items-center gap-1"><Briefcase size={13} /> {job.sector}</span>
              <span className="flex items-center gap-1"><Clock size={13} /> {new Date(job.created_at).toLocaleDateString('fr-FR')}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="badge badge-green">{job.contract_type}</span>
            <span className="badge badge-blue capitalize">{job.experience_level}</span>
          </div>
        </div>

        {job.salary_min && job.salary_max && (
          <p className="text-green-700 font-semibold text-sm mb-4">
            Salaire : {job.salary_min.toLocaleString()} – {job.salary_max.toLocaleString()} DT/mois
          </p>
        )}

        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">{job.description}</p>
      </div>

      {/* Compétences requises */}
      {job.required_skills?.length > 0 && (
        <div className="card mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">Compétences requises</h2>
          <div className="flex flex-wrap gap-2">
            {job.required_skills.map((s) => (
              <span key={s} className="badge badge-blue">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Zone candidature */}
      {isCandidat && !applied && (
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">Postuler à cette offre</h2>

          <div className="mb-4">
            <label className="form-label">Sélectionner un CV</label>
            {cvs.length === 0 ? (
              <div className="p-4 bg-yellow-50 rounded-lg text-sm text-yellow-700">
                Vous n'avez pas encore de CV.{' '}
                <Link to="/my-cvs" className="font-medium underline">Ajouter un CV</Link>
              </div>
            ) : (
              <select className="form-input" value={selectedCV} onChange={(e) => setSelected(e.target.value)}>
                <option value="">-- Choisir un CV --</option>
                {cvs.map((cv) => (
                  <option key={cv.id} value={cv.id}>
                    {cv.original_name} {cv.is_primary ? '(principal)' : ''}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="mb-4">
            <label className="form-label">Lettre de motivation (optionnel)</label>
            <textarea
              rows={4}
              className="form-input resize-none"
              placeholder="Expliquez pourquoi vous êtes le candidat idéal..."
              value={coverLetter}
              onChange={(e) => setCover(e.target.value)}
            />
          </div>

          <button
            onClick={handleApply}
            disabled={applying || !selectedCV}
            className="btn btn-primary btn-lg w-full"
          >
            {applying
              ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              : <><Send size={16} /> Envoyer ma candidature</>
            }
          </button>
        </div>
      )}

      {applied && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center gap-3 text-green-700">
            <CheckCircle size={24} />
            <div>
              <p className="font-semibold">Candidature envoyée !</p>
              <p className="text-sm">Notre IA analyse votre CV et calcule votre score de compatibilité. Vous serez notifié(e) par email.</p>
            </div>
          </div>
          <Link to="/my-applications" className="btn btn-secondary btn-sm mt-3">
            Voir mes candidatures
          </Link>
        </div>
      )}

      {!isAuthenticated && (
        <div className="card border-primary-100 bg-primary-50">
          <p className="text-primary-800 text-sm font-medium">
            <Link to="/login" className="underline">Connectez-vous</Link> pour postuler à cette offre.
          </p>
        </div>
      )}
    </div>
  )
}
