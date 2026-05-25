import { UpdatePasswordForm } from '@/components/auth/UpdatePasswordForm'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Atualizar Senha - DataMaster Pro',
  description: 'Crie uma nova senha para sua conta',
}

export default function UpdatePasswordPage() {
  return <UpdatePasswordForm />
}
