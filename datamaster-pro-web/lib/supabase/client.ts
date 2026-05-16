import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)

export type Database = {
  public: {
    Tables: {
      usuarios: {
        Row: {
          id: string
          email: string
          nome: string
          plano: 'free' | 'basico' | 'pro' | 'enterprise'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          nome: string
          plano?: 'free' | 'basico' | 'pro' | 'enterprise'
        }
        Update: {
          id?: string
          email?: string
          nome?: string
          plano?: 'free' | 'basico' | 'pro' | 'enterprise'
        }
      }
      executions: {
        Row: {
          id: string
          user_id: string
          tool: string
          status: 'pending' | 'completed' | 'failed'
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          tool: string
          status?: 'pending' | 'completed' | 'failed'
        }
        Update: {
          id?: string
          user_id?: string
          tool?: string
          status?: 'pending' | 'completed' | 'failed'
        }
      }
    }
  }
}