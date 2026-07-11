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
          plano_tipo: 'gratis' | 'starter' | 'pro'
          empresa: string | null
          preferencias_tema: string
          notificacoes_email: boolean
          notificacoes_desktop: boolean
          data_expiracao: string | null
          ultima_sincronizacao: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          nome: string
          plano_tipo?: 'gratis' | 'starter' | 'pro'
          empresa?: string
          preferencias_tema?: string
          notificacoes_email?: boolean
          notificacoes_desktop?: boolean
        }
        Update: {
          id?: string
          email?: string
          nome?: string
          plano_tipo?: 'gratis' | 'starter' | 'pro'
          empresa?: string
          preferencias_tema?: string
          notificacoes_email?: boolean
          notificacoes_desktop?: boolean
          data_expiracao?: string
          ultima_sincronizacao?: string
          updated_at?: string
        }
      }
      execucoes: {
        Row: {
          id: string
          usuario_id: string
          ferramenta: string
          status: string
          created_at: string
        }
        Insert: {
          id?: string
          usuario_id: string
          ferramenta: string
          status?: string
        }
        Update: {
          id?: string
          usuario_id?: string
          ferramenta?: string
          status?: string
        }
      }
      pagamentos: {
        Row: {
          id: string
          usuario_id: string
          plano: string
          valor: number
          status: string
          transacao_id: string
          gateway: string
          metadata: string
          created_at: string
        }
        Insert: {
          id?: string
          usuario_id: string
          plano: string
          valor: number
          status: string
          transacao_id: string
          gateway: string
          metadata?: string
        }
        Update: {
          id?: string
          usuario_id?: string
          plano?: string
          valor?: number
          status?: string
          transacao_id?: string
          gateway?: string
          metadata?: string
        }
      }
      consent_logs: {
        Row: {
          id: string
          user_id: string
          necessary: boolean
          analytics: boolean
          marketing: boolean
          ip_address: string
          user_agent: string
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          necessary: boolean
          analytics: boolean
          marketing: boolean
          ip_address?: string
          user_agent?: string
        }
        Update: {
          id?: string
          user_id?: string
          necessary?: boolean
          analytics?: boolean
          marketing?: boolean
        }
      }
      execution_logs: {
        Row: {
          execution_id: string
          user_id: string
          tool_name: string
          timestamp: string
          duration_seconds: number
          lines_processed: number
          file_size_bytes: number
          status: string
          error_message: string | null
          created_at: string
        }
        Insert: {
          execution_id?: string
          user_id: string
          tool_name: string
          timestamp: string
          duration_seconds: number
          lines_processed?: number
          file_size_bytes?: number
          status: string
          error_message?: string
        }
        Update: {
          execution_id?: string
          user_id?: string
          tool_name?: string
          timestamp?: string
          duration_seconds?: number
          lines_processed?: number
          file_size_bytes?: number
          status?: string
          error_message?: string
        }
      }
      scheduled_tasks: {
        Row: {
          task_id: string
          user_id: string
          tool_name: string
          tool_action: string
          task_name: string | null
          input_files: string
          schedule_frequency: string
          cron_expression: string | null
          time_of_day: string | null
          day_of_week: number | null
          day_of_month: number | null
          enabled: boolean
          last_run: string | null
          next_run: string
          execution_count: number
          last_status: string | null
          last_error: string | null
          config: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          task_id?: string
          user_id: string
          tool_name: string
          tool_action: string
          task_name?: string
          input_files: string
          schedule_frequency: string
          cron_expression?: string
          time_of_day?: string
          day_of_week?: number
          day_of_month?: number
          enabled?: boolean
          last_run?: string
          next_run: string
          execution_count?: number
          last_status?: string
          last_error?: string
          config?: string
        }
        Update: {
          task_id?: string
          user_id?: string
          tool_name?: string
          tool_action?: string
          task_name?: string
          input_files?: string
          schedule_frequency?: string
          cron_expression?: string
          time_of_day?: string
          day_of_week?: number
          day_of_month?: number
          enabled?: boolean
          last_run?: string
          next_run?: string
          execution_count?: number
          last_status?: string
          last_error?: string
          config?: string
          updated_at?: string
        }
      }
      webhooks_log: {
        Row: {
          id: string
          fonte: string
          tipo_evento: string
          payload: Record<string, unknown>
          processado: boolean
          created_at: string
        }
        Insert: {
          id?: string
          fonte: string
          tipo_evento: string
          payload: Record<string, unknown>
          processado?: boolean
        }
        Update: {
          id?: string
          fonte?: string
          tipo_evento?: string
          payload?: Record<string, unknown>
          processado?: boolean
        }
      }
    }
  }
}
