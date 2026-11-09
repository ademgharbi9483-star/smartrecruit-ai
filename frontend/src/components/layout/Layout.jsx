import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import { useAuth } from '../../context/AuthContext'

export default function Layout() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="flex flex-1 pt-16">
        {isAuthenticated && <Sidebar />}
        <main className={`flex-1 p-6 ${isAuthenticated ? 'ml-64' : ''}`}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
