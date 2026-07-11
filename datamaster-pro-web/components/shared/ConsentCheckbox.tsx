'use client'

import { useState } from 'react'
import Link from 'next/link'

interface ConsentCheckboxProps {
  onChange?: (checked: boolean) => void
  error?: string
}

export function ConsentCheckbox({ onChange, error }: ConsentCheckboxProps) {
  const [checked, setChecked] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(e.target.checked)
    onChange?.(e.target.checked)
  }

  return (
    <div className="space-y-2">
      <label className="flex items-start gap-3 cursor-pointer select-none group">
        <input
          type="checkbox"
          checked={checked}
          onChange={handleChange}
          className="mt-1 h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500 focus:ring-offset-0"
          aria-describedby="consent-description"
        />
        <span id="consent-description" className="text-xs text-surface-500 leading-relaxed">
          Li e aceito os{' '}
          <Link href="/termos" className="underline font-medium text-surface-700 hover:text-primary-600" target="_blank" rel="noopener noreferrer">
            Termos de Uso
          </Link>{' '}
          e a{' '}
          <Link href="/privacidade" className="underline font-medium text-surface-700 hover:text-primary-600" target="_blank" rel="noopener noreferrer">
            Politica de Privacidade
          </Link>
          . Consinto com o tratamento dos meus dados pessoais conforme descrito nessas politicas.{' '}
          <span className="text-red-500">*</span>
        </span>
      </label>
      {error && (
        <p className="text-xs text-red-600 ml-7" role="alert">{error}</p>
      )}
    </div>
  )
}
