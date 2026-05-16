import { AuthForm } from '@/components/auth/AuthForm'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Criar conta - DataMaster Pro',
  description: 'Crie sua conta DataMaster Pro e comece a usar todas as ferramentas',
}

export default function RegisterPage() {
  return <AuthForm mode="register" />
}