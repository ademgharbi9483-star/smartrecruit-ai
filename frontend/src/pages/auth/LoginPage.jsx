import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate   = useNavigate()
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading]   = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const user = await login(data.email, data.password)
      toast.success(`Bienvenue, ${user.full_name} !`)
      if (user.role === 'candidat')  navigate('/jobs')
      else if (user.role === 'recruteur') navigate('/dashboard')
      else navigate('/')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Email ou mot de passe incorrect.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Connexion</h1>
      <p className="text-gray-500 text-sm mb-6">Accédez à votre espace SmartRecruit AI.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {/* Email */}
        <div>
          <label className="form-label">Adresse email</label>
          <input
            type="email"
            className={`form-input ${errors.email ? 'border-red-400 focus:ring-red-400' : ''}`}
            placeholder="vous@exemple.com"
            {...register('email', {
              required: "L'email est requis.",
              pattern: { value: /^\S+@\S+\.\S+$/, message: "Email invalide." },
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
              className={`form-input pr-10 ${errors.password ? 'border-red-400 focus:ring-red-400' : ''}`}
              placeholder="••••••••"
              {...register('password', { required: "Le mot de passe est requis." })}
            />
            <button
              type="button"
              onClick={() => setShowPass((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {errors.password && <p className="form-error">{errors.password.message}</p>}
        </div>

        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-xs text-primary-600 hover:underline">
            Mot de passe oublié ?
          </Link>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full btn-lg"
        >
          {loading ? (
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
            <><LogIn size={16} /> Se connecter</>
          )}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Pas encore de compte ?{' '}
        <Link to="/register" className="text-primary-600 font-medium hover:underline">
          Créer un compte
        </Link>
      </p>
    </div>
  )
}
