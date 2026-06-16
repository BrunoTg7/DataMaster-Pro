import { Loader2 } from 'lucide-react'

export default function Loading() {
  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-10 h-10 text-primary-500 animate-spin mx-auto mb-4" />
        <p className="text-surface-600 font-medium">Carregando...</p>
      </div>
    </div>
  )
}
