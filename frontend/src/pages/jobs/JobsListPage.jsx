import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Search, MapPin, Briefcase, Clock, ChevronRight, Filter } from 'lucide-react'
import { jobsAPI } from '../../services/api'
import toast from 'react-hot-toast'

function JobCard({ job }) {
  const contractColors = {
    CDI: 'badge-green', CDD: 'badge-blue', Freelance: 'badge-purple',
    Stage: 'badge-yellow', Alternance: 'badge-purple',
  }

  return (
    <Link
      to={`/jobs/${job.id}`}
      className="card-hover flex flex-col gap-4 group"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
            {job.title}
          </h3>
          <p className="text-sm text-gray-500 mt-0.5">{job.recruiter_name || 'Entreprise'}</p>
        </div>
        <span className={contractColors[job.contract_type] || 'badge-gray'}>
          {job.contract_type}
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <MapPin size={12} /> {job.location}
        </span>
        <span className="flex items-center gap-1">
          <Briefcase size={12} /> {job.sector}
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} /> {new Date(job.created_at).toLocaleDateString('fr-FR')}
        </span>
      </div>

      {job.required_skills?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {job.required_skills.slice(0, 4).map((s) => (
            <span key={s} className="badge badge-gray">{s}</span>
          ))}
          {job.required_skills.length > 4 && (
            <span className="badge badge-gray">+{job.required_skills.length - 4}</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
        {job.salary_min && job.salary_max ? (
          <span className="text-sm font-medium text-green-700">
            {job.salary_min.toLocaleString()} – {job.salary_max.toLocaleString()} DT/mois
          </span>
        ) : <span />}
        <span className="text-xs text-primary-600 font-medium flex items-center gap-1">
          Voir l'offre <ChevronRight size={12} />
        </span>
      </div>
    </Link>
  )
}

export default function JobsListPage() {
  const [jobs, setJobs]         = useState([])
  const [loading, setLoading]   = useState(true)
  const [total, setTotal]       = useState(0)
  const [filters, setFilters]   = useState({
    search: '', location: '', contract_type: '', sector: '', experience_level: '',
  })
  const [page, setPage] = useState(1)

  useEffect(() => {
    fetchJobs()
  }, [filters, page])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const params = { page, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
      const res = await jobsAPI.list(params)
      setJobs(res.data.results)
      setTotal(res.data.count)
    } catch {
      toast.error('Erreur lors du chargement des offres.')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }))
    setPage(1)
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Offres d'emploi</h1>
        <p className="text-gray-500 text-sm mt-1">{total} offre{total !== 1 ? 's' : ''} disponible{total !== 1 ? 's' : ''}</p>
      </div>

      {/* Recherche + Filtres */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Titre, compétence, entreprise..."
              className="form-input pl-9"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          <select
            className="form-input w-full sm:w-40"
            value={filters.contract_type}
            onChange={(e) => handleFilterChange('contract_type', e.target.value)}
          >
            <option value="">Type contrat</option>
            {['CDI', 'CDD', 'Freelance', 'Stage', 'Alternance'].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <select
            className="form-input w-full sm:w-40"
            value={filters.experience_level}
            onChange={(e) => handleFilterChange('experience_level', e.target.value)}
          >
            <option value="">Expérience</option>
            <option value="junior">Junior</option>
            <option value="mid">Confirmé</option>
            <option value="senior">Senior</option>
          </select>

          <input
            type="text"
            placeholder="Localisation"
            className="form-input w-full sm:w-36"
            value={filters.location}
            onChange={(e) => handleFilterChange('location', e.target.value)}
          />
        </div>
      </div>

      {/* Liste */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Briefcase size={40} className="mx-auto mb-3 opacity-30" />
          <p>Aucune offre ne correspond à vos critères.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {jobs.map((job) => <JobCard key={job.id} job={job} />)}
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn btn-secondary btn-sm"
          >
            Précédent
          </button>
          <span className="text-sm text-gray-500 self-center">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={jobs.length < 20}
            className="btn btn-secondary btn-sm"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  )
}
