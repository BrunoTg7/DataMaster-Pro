'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ShieldCheck, X, Settings } from 'lucide-react'

interface CookieConsent {
  necessary: boolean
  analytics: boolean
  marketing: boolean
}

export function ConsentBanner() {
  const [isVisible, setIsVisible] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const [preferences, setPreferences] = useState<CookieConsent>({
    necessary: true,
    analytics: false,
    marketing: false,
  })

  useEffect(() => {
    const consent = localStorage.getItem('datamaster_consent_v2')
    if (!consent) {
      const timer = setTimeout(() => {
        setIsVisible(true)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [])

  const saveConsent = (prefs: CookieConsent) => {
    localStorage.setItem('datamaster_consent_v2', JSON.stringify(prefs))
    localStorage.setItem('datamaster_consent', 'true')
  }

  const handleAcceptAll = () => {
    const allAccepted = { necessary: true, analytics: true, marketing: true }
    setPreferences(allAccepted)
    saveConsent(allAccepted)
    setIsVisible(false)
  }

  const handleAcceptSelected = () => {
    saveConsent(preferences)
    setIsVisible(false)
  }

  const handleDecline = () => {
    const onlyNecessary = { necessary: true, analytics: false, marketing: false }
    setPreferences(onlyNecessary)
    saveConsent(onlyNecessary)
    setIsVisible(false)
  }

  if (!isVisible) return null

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-lg z-[100] animate-in slide-in-from-bottom-5 duration-300">
      <div className="bg-white/95 dark:bg-surface-900/95 backdrop-blur-xl border border-surface-200/50 dark:border-surface-800/50 shadow-2xl rounded-2xl p-5 flex flex-col gap-4 text-surface-700 dark:text-surface-200">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-lg shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <h3 className="font-semibold text-surface-900 dark:text-white text-sm">Privacidade e Cookies (LGPD)</h3>
              <button
                onClick={handleDecline}
                className="text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 transition-colors p-1"
                aria-label="Fechar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-surface-600 dark:text-surface-400 leading-relaxed">
              Utilizamos cookies para melhorar sua experiencia, analisar trafego e garantir conformidade com a LGPD.{' '}
              <Link href="/cookies" className="text-primary-600 dark:text-primary-400 underline font-medium hover:text-primary-700 dark:hover:text-primary-300">
                Politica de Cookies
              </Link>
            </p>
          </div>
        </div>

        {showDetails && (
          <div className="space-y-3 px-1">
            <div className="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800 rounded-lg">
              <div>
                <p className="text-xs font-semibold text-surface-900 dark:text-white">Cookies Necessarios</p>
                <p className="text-[10px] text-surface-500">Essenciais para o funcionamento do site.</p>
              </div>
              <input
                type="checkbox"
                checked={preferences.necessary}
                disabled
                className="h-4 w-4 rounded border-surface-300 text-primary-600"
                aria-label="Cookies necessarios (sempre ativos)"
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800 rounded-lg">
              <div>
                <p className="text-xs font-semibold text-surface-900 dark:text-white">Cookies de Analise</p>
                <p className="text-[10px] text-surface-500">Nos ajudam a entender como voce usa o site.</p>
              </div>
              <input
                type="checkbox"
                checked={preferences.analytics}
                onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
                aria-label="Cookies de analise"
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800 rounded-lg">
              <div>
                <p className="text-xs font-semibold text-surface-900 dark:text-white">Cookies de Marketing</p>
                <p className="text-[10px] text-surface-500">Usados para personalizar anuncios.</p>
              </div>
              <input
                type="checkbox"
                checked={preferences.marketing}
                onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
                aria-label="Cookies de marketing"
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 text-xs">
          {!showDetails ? (
            <button
              onClick={() => setShowDetails(true)}
              className="px-3 py-2 text-surface-500 hover:text-surface-700 dark:hover:text-surface-300 flex items-center gap-1 transition-colors"
            >
              <Settings className="w-3 h-3" /> Personalizar
            </button>
          ) : (
            <button
              onClick={handleAcceptSelected}
              className="px-3 py-2 text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg font-medium transition-colors"
            >
              Salvar Preferencias
            </button>
          )}
          <button
            onClick={handleDecline}
            className="px-3 py-2 text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg font-medium transition-colors"
          >
            Recusar
          </button>
          <button
            onClick={handleAcceptAll}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-lg shadow-primary-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Aceitar Todos
          </button>
        </div>
      </div>
    </div>
  )
}
