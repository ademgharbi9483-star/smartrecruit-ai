import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-8xl font-black text-primary-200">404</h1>
        <h2 className="text-2xl font-bold text-gray-900 mt-4">Page introuvable</h2>
        <p className="text-gray-500 mt-2">La page que vous cherchez n'existe pas.</p>
        <Link to="/" className="btn btn-primary mt-6 inline-flex">Retour à l'accueil</Link>
      </div>
    </div>
  )
}
