import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Plus, X, Briefcase } from 'lucide-react'
import { jobsAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function CreateJobPage() {
  const navigate = useNavigate()
  const [skills, setSkills]     = useState([])
  const [skillInput, setSkillInput] = useState('')
  const [loading, setLoading]   = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm()

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !skills.includes(s)) {
      setSkills((prev) => [...prev, s])
      setSkillInput('')
    }
  }
  const removeSkill = (s) => setSkills((prev) => prev.filter((x) => x !== s))

  const onSubmit = async (data) => {
    if (skills.length === 0) return toast.error('Ajoutez au moins une compétence requise.')
    setLoading(true)
    try {
      await jobsAPI.create({ ...data, required_skills: skills })
      toast.success('Offre publiée avec succès !')
      navigate('/jobs/my-offers')
    } catch (err) {
      const errs = err.response?.data
      const first = errs ? Object.values(errs).flat()[0] : 'Erreur lors de la création.'
      toast.error(typeof first === 'string' ? first : 'Erreur lors de la création.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Publier une offre d'emploi</h1>
        <p className="text-gray-500 text-sm mt-1">Notre IA analysera automatiquement les candidatures reçues.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div className="card space-y-5">
          {/* Titre */}
          <div>
            <label className="form-label">Titre du poste *</label>
            <input
              type="text"
              className={`form-input ${errors.title ? 'border-red-400' : ''}`}
              placeholder="Ex. Développeur Python Senior"
              {...register('title', { required: 'Requis.' })}
            />
            {errors.title && <p className="form-error">{errors.title.message}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="form-label">Description du poste *</label>
            <textarea
              rows={5}
              className={`form-input resize-none ${errors.description ? 'border-red-400' : ''}`}
              placeholder="Décrivez les responsabilités, le profil recherché..."
              {...register('description', { required: 'Requis.', minLength: { value: 50, message: '50 caractères minimum.' } })}
            />
            {errors.description && <p className="form-error">{errors.description.message}</p>}
          </div>

          {/* Grille 2 colonnes */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">Localisation *</label>
              <input
                type="text"
                className="form-input"
                placeholder="Tunis, Remote..."
                {...register('location', { required: 'Requis.' })}
              />
            </div>
            <div>
              <label className="form-label">Secteur *</label>
              <input
                type="text"
                className="form-input"
                placeholder="Informatique, Finance..."
                {...register('sector', { required: 'Requis.' })}
              />
            </div>
            <div>
              <label className="form-label">Type de contrat *</label>
              <select className="form-input" {...register('contract_type', { required: 'Requis.' })}>
                <option value="">--</option>
                {['CDI', 'CDD', 'Freelance', 'Stage', 'Alternance'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="form-label">Niveau d'expérience *</label>
              <select className="form-input" {...register('experience_level', { required: 'Requis.' })}>
                <option value="">--</option>
                <option value="junior">Junior (0-2 ans)</option>
                <option value="mid">Confirmé (2-5 ans)</option>
                <option value="senior">Senior (5+ ans)</option>
              </select>
            </div>
            <div>
              <label className="form-label">Salaire min (DT)</label>
              <input type="number" className="form-input" placeholder="2000" {...register('salary_min', { min: { value: 0, message: 'Invalide' } })} />
            </div>
            <div>
              <label className="form-label">Salaire max (DT)</label>
              <input type="number" className="form-input" placeholder="5000" {...register('salary_max', { min: { value: 0, message: 'Invalide' } })} />
            </div>
          </div>
        </div>

        {/* Compétences */}
        <div className="card">
          <label className="form-label">Compétences requises *</label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              className="form-input flex-1"
              placeholder="Ex. Python, React, Docker..."
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
            />
            <button type="button" onClick={addSkill} className="btn btn-secondary">
              <Plus size={14} /> Ajouter
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <span key={s} className="flex items-center gap-1 badge badge-blue">
                {s}
                <button type="button" onClick={() => removeSkill(s)} className="hover:text-red-500">
                  <X size={10} />
                </button>
              </span>
            ))}
            {skills.length === 0 && (
              <p className="text-xs text-gray-400">Aucune compétence ajoutée. Appuyez sur Entrée ou cliquez Ajouter.</p>
            )}
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary btn-lg w-full">
          {loading
            ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            : <><Briefcase size={16} /> Publier l'offre</>
          }
        </button>
      </form>
    </div>
  )
}
