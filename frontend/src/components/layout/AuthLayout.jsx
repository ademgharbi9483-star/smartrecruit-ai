import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-500/5 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-2xl font-bold text-primary-700">
            <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center text-white font-black text-sm">
              SR
            </div>
            SmartRecruit AI
          </div>
          <p className="text-gray-500 text-sm mt-1">Recrutement intelligent, simplifié.</p>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
