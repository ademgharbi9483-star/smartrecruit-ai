import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/layout/Layout'
import AuthLayout from './components/layout/AuthLayout'

// Pages Auth
import LoginPage    from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'

// Pages Jobs
import JobsListPage   from './pages/jobs/JobsListPage'
import JobDetailPage  from './pages/jobs/JobDetailPage'
import CreateJobPage  from './pages/jobs/CreateJobPage'
import MyJobsPage     from './pages/jobs/MyJobsPage'

// Pages Candidates
import MyCVsPage          from './pages/candidates/MyCVsPage'
import MyApplicationsPage from './pages/candidates/MyApplicationsPage'
import CandidateProfilePage from './pages/candidates/CandidateProfilePage'

// Pages Dashboard
import RecruiterDashboard from './pages/dashboard/RecruiterDashboard'
import JobApplicationsPage from './pages/dashboard/JobApplicationsPage'

// Pages Chatbot
import ChatbotPage from './pages/chatbot/ChatbotPage'

// Misc
import NotFoundPage from './pages/NotFoundPage'
import HomePage     from './pages/HomePage'

function PrivateRoute({ children, roles }) {
  const { isAuthenticated, user, loading } = useAuth()
  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
    </div>
  )
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user?.role)) return <Navigate to="/" replace />
  return children
}

function PublicOnlyRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return null
  if (isAuthenticated) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* ── Auth ── */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={
            <PublicOnlyRoute><LoginPage /></PublicOnlyRoute>
          } />
          <Route path="/register" element={
            <PublicOnlyRoute><RegisterPage /></PublicOnlyRoute>
          } />
        </Route>

        {/* ── App ── */}
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />

          {/* Offres */}
          <Route path="/jobs" element={<JobsListPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/jobs/create" element={
            <PrivateRoute roles={['recruteur', 'admin']}><CreateJobPage /></PrivateRoute>
          } />
          <Route path="/jobs/my-offers" element={
            <PrivateRoute roles={['recruteur', 'admin']}><MyJobsPage /></PrivateRoute>
          } />

          {/* Candidat */}
          <Route path="/my-cvs" element={
            <PrivateRoute roles={['candidat']}><MyCVsPage /></PrivateRoute>
          } />
          <Route path="/my-applications" element={
            <PrivateRoute roles={['candidat']}><MyApplicationsPage /></PrivateRoute>
          } />
          <Route path="/profile" element={
            <PrivateRoute roles={['candidat']}><CandidateProfilePage /></PrivateRoute>
          } />

          {/* Recruteur Dashboard */}
          <Route path="/dashboard" element={
            <PrivateRoute roles={['recruteur', 'admin']}><RecruiterDashboard /></PrivateRoute>
          } />
          <Route path="/dashboard/jobs/:jobId/applications" element={
            <PrivateRoute roles={['recruteur', 'admin']}><JobApplicationsPage /></PrivateRoute>
          } />

          {/* Chatbot */}
          <Route path="/chatbot" element={
            <PrivateRoute><ChatbotPage /></PrivateRoute>
          } />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  )
}
