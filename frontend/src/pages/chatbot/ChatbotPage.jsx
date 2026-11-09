import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, RefreshCw, AlertCircle } from 'lucide-react'
import { aiAPI } from '../../services/api'
import { useAuth } from '../../context/AuthContext'

function ChatBubble({ msg }) {
  const isBot = msg.role === 'bot'
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} gap-3`}>
      {isBot && (
        <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center shrink-0 mt-1">
          <Bot size={16} className="text-primary-600" />
        </div>
      )}
      <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
        isBot
          ? 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-tl-sm'
          : 'bg-primary-600 text-white rounded-tr-sm'
      }`}>
        {msg.text}
        {msg.needs_escalation && (
          <div className="flex items-center gap-1 mt-2 text-orange-600 text-xs">
            <AlertCircle size={12} />
            Transfert à un recruteur en cours...
          </div>
        )}
      </div>
      {!isBot && (
        <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center shrink-0 mt-1">
          <User size={16} className="text-white" />
        </div>
      )}
    </div>
  )
}

const SUGGESTIONS = [
  "Quel est le statut de ma candidature ?",
  "Comment déposer mon CV ?",
  "Comment est calculé mon score ?",
  "Comment postuler à une offre ?",
]

export default function ChatbotPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    {
      id: 0, role: 'bot',
      text: `Bonjour ${user?.full_name?.split(' ')[0] || ''} ! Je suis le chatbot RH de SmartRecruit AI. Comment puis-je vous aider ?`,
    },
  ])
  const [input, setInput]   = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return

    setInput('')
    setMessages((prev) => [...prev, { id: Date.now(), role: 'user', text: msg }])
    setLoading(true)

    try {
      const res = await aiAPI.chatbot(msg)
      const { answer, needs_escalation } = res.data
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'bot', text: answer, needs_escalation },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'bot', text: "Désolé, je rencontre un problème technique. Veuillez réessayer." },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setMessages([{
      id: 0, role: 'bot',
      text: `Bonjour ${user?.full_name?.split(' ')[0] || ''} ! Nouvelle conversation. Comment puis-je vous aider ?`,
    }])
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col h-[calc(100vh-7rem)]">
      {/* En-tête */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
            <Bot size={20} className="text-primary-600" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">Chatbot RH</h1>
            <p className="text-xs text-green-500 font-medium">● En ligne</p>
          </div>
        </div>
        <button onClick={handleReset} className="btn btn-ghost btn-sm text-gray-400">
          <RefreshCw size={13} /> Nouvelle conversation
        </button>
      </div>

      {/* Zone de messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-xl border border-gray-100 mb-4">
        {messages.map((msg) => <ChatBubble key={msg.id} msg={msg} />)}

        {loading && (
          <div className="flex justify-start gap-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center shrink-0">
              <Bot size={16} className="text-primary-600" />
            </div>
            <div className="bg-white border border-gray-100 shadow-sm px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1">
                {[0, 0.15, 0.3].map((delay, i) => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions rapides */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => sendMessage(s)}
              className="text-xs bg-white border border-gray-200 px-3 py-1.5 rounded-full text-gray-600 hover:border-primary-300 hover:text-primary-600 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Saisie */}
      <div className="flex gap-3">
        <input
          type="text"
          className="form-input flex-1"
          placeholder="Posez votre question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          disabled={loading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          className="btn btn-primary"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
