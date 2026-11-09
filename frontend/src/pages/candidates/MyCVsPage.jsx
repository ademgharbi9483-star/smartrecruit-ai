import { useEffect, useState, useRef } from 'react'
import { Upload, Trash2, RefreshCw, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { candidatesAPI } from '../../services/api'
import toast from 'react-hot-toast'

const statusIcon = {
  done:       <CheckCircle size={14} className="text-green-500" />,
  processing: <Clock size={14} className="text-yellow-500 animate-pulse" />,
  pending:    <Clock size={14} className="text-gray-400" />,
  failed:     <AlertCircle size={14} className="text-red-500" />,
}

const statusLabel = {
  done: 'Analysé', processing: 'En cours...', pending: 'En attente', failed: 'Échec',
}

export default function MyCVsPage() {
  const [cvs, setCVs]         = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => { fetchCVs() }, [])

  const fetchCVs = async () => {
    try {
      const res = await candidatesAPI.listCVs()
      setCVs(res.data.results || res.data)
    } catch { toast.error('Erreur lors du chargement des CV.') }
    finally { setLoading(false) }
  }

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.pdf')) return toast.error('Seuls les fichiers PDF sont acceptés.')
    if (file.size > 10 * 1024 * 1024) return toast.error('Taille max : 10 Mo.')

    const fd = new FormData()
    fd.append('file', file)
    fd.append('is_primary', cvs.length === 0 ? 'true' : 'false')

    setUploading(true)
    try {
      const res = await candidatesAPI.uploadCV(fd)
      setCVs((prev) => [...prev, res.data])
      toast.success('CV uploadé ! Analyse IA en cours...')
      // Polling léger pour mettre à jour le statut
      setTimeout(fetchCVs, 5000)
    } catch (err) {
      const msg = err.response?.data?.file?.[0] || 'Erreur lors de l\'upload.'
      toast.error(msg)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (cv) => {
    if (!confirm(`Supprimer "${cv.original_name}" ?`)) return
    try {
      await candidatesAPI.deleteCV(cv.id)
      setCVs((prev) => prev.filter((c) => c.id !== cv.id))
      toast.success('CV supprimé.')
    } catch { toast.error('Erreur lors de la suppression.') }
  }

  const handleReanalyze = async (cv) => {
    try {
      await candidatesAPI.reanalyzeCV(cv.id)
      setCVs((prev) => prev.map((c) => c.id === cv.id ? { ...c, processing_status: 'pending' } : c))
      toast.success('Analyse relancée.')
      setTimeout(fetchCVs, 5000)
    } catch { toast.error('Erreur lors de la relance.') }
  }

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mes CV</h1>
          <p className="text-gray-500 text-sm mt-1">Uploadez votre CV pour postuler aux offres.</p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="btn btn-primary"
        >
          {uploading
            ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            : <><Upload size={14} /> Ajouter un CV</>
          }
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleUpload}
        />
      </div>

      {cvs.length === 0 ? (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center cursor-pointer hover:border-primary-300 hover:bg-primary-50/30 transition-all"
        >
          <Upload size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 font-medium">Glissez-déposez ou cliquez pour uploader</p>
          <p className="text-gray-400 text-xs mt-1">PDF uniquement, max 10 Mo</p>
        </div>
      ) : (
        <div className="space-y-3">
          {cvs.map((cv) => (
            <div key={cv.id} className="card flex items-center gap-4">
              <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center shrink-0">
                <FileText size={20} className="text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-900 text-sm truncate">{cv.original_name}</p>
                  {cv.is_primary && <span className="badge badge-blue">Principal</span>}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  {statusIcon[cv.processing_status]}
                  <span className="text-xs text-gray-400">{statusLabel[cv.processing_status] || cv.processing_status}</span>
                  {cv.file_size && (
                    <span className="text-xs text-gray-300">· {(cv.file_size / 1024).toFixed(0)} Ko</span>
                  )}
                </div>
                {cv.extracted_data?.skills?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {cv.extracted_data.skills.slice(0, 6).map((s) => (
                      <span key={s} className="badge badge-gray">{s}</span>
                    ))}
                    {cv.extracted_data.skills.length > 6 && (
                      <span className="badge badge-gray">+{cv.extracted_data.skills.length - 6}</span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {cv.processing_status === 'failed' && (
                  <button
                    onClick={() => handleReanalyze(cv)}
                    className="btn btn-ghost btn-sm text-primary-600"
                    title="Relancer l'analyse"
                  >
                    <RefreshCw size={13} />
                  </button>
                )}
                <button
                  onClick={() => handleDelete(cv)}
                  className="btn btn-ghost btn-sm text-red-500"
                  title="Supprimer"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
