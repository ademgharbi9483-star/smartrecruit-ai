import { Link } from 'react-router-dom'
import { Briefcase, Brain, BarChart2, MessageSquare, ArrowRight } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

function FeatureCard({ icon: Icon, title, desc, color }) {
  const bg = { blue: 'bg-blue-50 text-blue-600', purple: 'bg-purple-50 text-purple-600', green: 'bg-green-50 text-green-600', orange: 'bg-orange-50 text-orange-600' }
  return (
    <div className="card-hover">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${bg[color]}`}>
        <Icon size={20} />
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
    </div>
  )
}

export default function HomePage() {
  const { isAuthenticated, isCandidat, isRecruteur } = useAuth()

  return (
    <div className="max-w-5xl mx-auto">
      {/* Hero */}
      <div className="text-center py-12 mb-12">
        <span className="badge badge-blue mb-4">Recrutement intelligent · Propulsé par l'IA</span>
        <h1 className="text-4xl font-black text-gray-900 mb-4 leading-tight">
          Trouvez les meilleurs talents,<br/>
          <span className="text-primary-600">automatiquement.</span>
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
          SmartRecruit AI analyse les CV, calcule les scores de compatibilité et classe les candidats —
          pour que vous vous concentriez sur ce qui compte : rencontrer les bons profils.
        </p>
        <div className="flex flex-wrap gap-3 justify-center">
          {!isAuthenticated && (
            <>
              <Link to="/register" className="btn btn-primary btn-lg">
                Commencer gratuitement <ArrowRight size={16} />
              </Link>
              <Link to="/jobs" className="btn btn-secondary btn-lg">
                Explorer les offres
              </Link>
            </>
          )}
          {isCandidat && (
            <Link to="/jobs" className="btn btn-primary btn-lg">
              Voir les offres <ArrowRight size={16} />
            </Link>
          )}
          {isRecruteur && (
            <Link to="/dashboard" className="btn btn-primary btn-lg">
              Mon tableau de bord <ArrowRight size={16} />
            </Link>
          )}
        </div>
      </div>

      {/* Fonctionnalités */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">Ce que fait SmartRecruit AI</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <FeatureCard icon={Brain} title="Analyse IA des CV" color="blue"
            desc="Extraction automatique des compétences, formations et expériences via NLP et Sentence-BERT." />
          <FeatureCard icon={BarChart2} title="Score de compatibilité" color="purple"
            desc="Chaque candidature reçoit un score 0-100 basé sur la correspondance réelle avec l'offre." />
          <FeatureCard icon={Briefcase} title="Tableau de bord recruteur" color="green"
            desc="Visualisez tous vos candidats classés par score, filtrez et gérez leur statut en quelques clics." />
          <FeatureCard icon={MessageSquare} title="Chatbot RH 24/7" color="orange"
            desc="Les candidats obtiennent des réponses instantanées à leurs questions sans solliciter votre équipe." />
        </div>
      </div>

      {/* Stats */}
      <div className="bg-primary-600 rounded-2xl p-8 text-white text-center">
        <div className="grid grid-cols-3 gap-6">
          {[
            { value: '< 30s',  label: "Analyse d'un CV" },
            { value: '85%',    label: 'Précision extraction' },
            { value: '71%+',   label: 'Couverture de tests' },
          ].map(({ value, label }) => (
            <div key={label}>
              <p className="text-3xl font-black">{value}</p>
              <p className="text-primary-200 text-sm mt-1">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
