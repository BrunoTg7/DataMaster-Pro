import { AuthForm } from '@/components/auth/AuthForm'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Entrar - DataMaster Pro',
  description: 'Faça login na sua conta DataMaster Pro',
}

export default function LoginPage() {
  return <AuthForm mode="login" />
}