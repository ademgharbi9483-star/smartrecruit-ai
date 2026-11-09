import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { User, Save } from 'lucide-react'
import { candidatesAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function CandidateProfilePage() {
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const { register, handleSubmit, reset } = useForm()

  useEffect(() => {
    candidatesAPI.getProfile()
      .then((res) => reset(res.data))
      .catch(() => toast.error('Erreur de chargement du profil.'))
      .finally(() => setLoading(false))
  }, [])

  const onSubmit = async (data) => {
    setSaving(true)
    try {
      await candidatesAPI.updateProfile(data)
      toast.success('Profil mis à jour.')
    } catch { toast.error('Erreur lors de la mise à jour.') }
    finally { setSaving(false) }
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )

  return (
    <div className="max-w-xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Mon profil candidat</h1>
        <p className="text-gray-500 text-sm mt-1">Ces informations enrichissent vos candidatures.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="card space-y-4">
          <div>
            <label className="form-label">Titre professionnel</label>
            <input type="text" className="form-input" placeholder="Ex. Développeur Full-Stack Python / React" {...register('headline')} />
          </div>
          <div>
            <label className="form-label">Résumé</label>
            <textarea rows={4} className="form-input resize-none" placeholder="Présentez-vous en quelques lignes..." {...register('summary')} />
          </div>
          <div>
            <label className="form-label">Localisation</label>
            <input type="text" className="form-input" placeholder="Tunis, Remote..." {...register('location')} />
          </div>
        </div>

        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-900">Liens</h2>
          <div>
            <label className="form-label">LinkedIn</label>
            <input type="url" className="form-input" placeholder="https://linkedin.com/in/..." {...register('linkedin_url')} />
          </div>
          <div>
            <label className="form-label">GitHub</label>
            <input type="url" className="form-input" placeholder="https://github.com/..." {...register('github_url')} />
          </div>
          <div>
            <label className="form-label">Portfolio</label>
            <input type="url" className="form-input" placeholder="https://..." {...register('portfolio_url')} />
          </div>
        </div>

        <button type="submit" disabled={saving} className="btn btn-primary btn-lg w-full">
          {saving
            ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            : <><Save size={16} /> Enregistrer</>
          }
        </button>
      </form>
    </div>
  )
}
