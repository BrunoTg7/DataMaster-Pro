import { Metadata } from 'next'
import { BlogList } from './BlogList'

export const metadata: Metadata = {
  title: 'Blog - DataMaster Pro',
  description: 'Dicas, tutoriais e novidades sobre automação de planilhas e produtividade.',
}

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 pt-24 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-extrabold text-surface-900 dark:text-white mb-4">Blog & Insights</h1>
          <p className="text-lg text-surface-600 dark:text-surface-400">Compartilhando conhecimento para elevar sua produtividade.</p>
        </div>

        <BlogList />
      </div>
    </div>
  )
}
