import { ResetPasswordForm } from '@/components/auth/ResetPasswordForm'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Redefinir Senha - DataMaster Pro',
  description: 'Recupere o acesso à sua conta DataMaster Pro',
}

export default function ResetPasswordPage() {
  return <ResetPasswordForm />
}
