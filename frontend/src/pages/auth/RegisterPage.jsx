import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, UserPlus } from 'lucide-react'
import { authAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading]   = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({ defaultValues: { role: 'candidat' } })

  const password = watch('password')

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authAPI.register({
        email:      data.email,
        first_name: data.first_name,
        last_name:  data.last_name,
        role:       data.role,
        password:   data.password,
        password2:  data.password2,
      })
      toast.success('Compte créé avec succès ! Vous pouvez vous connecter.')
      navigate('/login')
    } catch (err) {
      const errors = err.response?.data
      if (errors) {
        const firstError = Object.values(errors).flat()[0]
        toast.error(typeof firstError === 'string' ? firstError : "Erreur lors de l'inscription.")
      } else {
        toast.error("Erreur lors de l'inscription.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Créer un compte</h1>
      <p className="text-gray-500 text-sm mb-6">Rejoignez SmartRecruit AI en quelques secondes.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {/* Rôle */}
        <div>
          <label className="form-label">Je suis</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'candidat', label: '👤 Candidat' },
              { value: 'recruteur', label: '🔍 Recruteur' },
            ].map(({ value, label }) => (
              <label
                key={value}
                className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer text-sm font-medium transition-all ${
                  watch('role') === value
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <input type="radio" className="sr-only" value={value} {...register('role')} />
                {label}
              </label>
            ))}
          </div>
        </div>

        {/* Noms */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="form-label">Prénom</label>
            <input
              type="text"
              className={`form-input ${errors.first_name ? 'border-red-400' : ''}`}
              placeholder="Alice"
              {...register('first_name', { required: 'Requis.' })}
            />
            {errors.first_name && <p className="form-error">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className="form-label">Nom</label>
            <input
              type="text"
              className={`form-input ${errors.last_name ? 'border-red-400' : ''}`}
              placeholder="Dupont"
              {...register('last_name', { required: 'Requis.' })}
            />
            {errors.last_name && <p className="form-error">{errors.last_name.message}</p>}
          </div>
        </div>

        {/* Email */}
        <div>
          <label className="form-label">Adresse email</label>
          <input
            type="email"
            className={`form-input ${errors.email ? 'border-red-400' : ''}`}
            placeholder="vous@exemple.com"
            {...register('email', {
              required: "L'email est requis.",
              pattern: { value: /^\S+@\S+\.\S+$/, message: 'Email invalide.' },
            })}
          />
          {errors.email && <p className="form-error">{errors.email.message}</p>}
        </div>

        {/* Mot de passe */}
        <div>
          <label className="form-label">Mot de passe</label>
          <div className="relative">
            <input
              type={showPass ? 'text' : 'password'}
              className={`form-input pr-10 ${errors.password ? 'border-red-400' : ''}`}
              placeholder="8 caractères minimum"
              {...register('password', {
                required: 'Requis.',
                minLength: { value: 8, message: '8 caractères minimum.' },
              })}
            />
            <button
              type="button"
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.password && <p className="form-error">{errors.password.message}</p>}
        </div>

        {/* Confirmation */}
        <div>
          <label className="form-label">Confirmer le mot de passe</label>
          <input
            type="password"
            className={`form-input ${errors.password2 ? 'border-red-400' : ''}`}
            placeholder="••••••••"
            {...register('password2', {
              required: 'Requis.',
              validate: (v) => v === password || 'Les mots de passe ne correspondent pas.',
            })}
          />
          {errors.password2 && <p className="form-error">{errors.password2.message}</p>}
        </div>

        <button type="submit" disabled={loading} className="btn btn-primary w-full btn-lg">
          {loading
            ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            : <><UserPlus size={16} /> Créer mon compte</>
          }
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Déjà un compte ?{' '}
        <Link to="/login" className="text-primary-600 font-medium hover:underline">
          Se connecter
        </Link>
      </p>
    </div>
  )
}
