import { Metadata } from 'next'
import Link from 'next/link'
import { Calendar, User, ArrowRight } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Blog - DataMaster Pro',
  description: 'Dicas, tutoriais e novidades sobre automação de planilhas e produtividade.',
}

const POSTS = [
  {
    id: 1,
    title: '5 Truques de Excel que você deveria saber em 2026',
    excerpt: 'Descubra como otimizar suas fórmulas e ganhar tempo com novas funções nativas.',
    author: 'Equipe DataMaster',
    date: '02 de Maio, 2026',
    category: 'Tutoriais',
    image: 'https://images.unsplash.com/photo-1543286386-713bdd548da4?auto=format&fit=crop&q=80&w=800',
  },
  {
    id: 2,
    title: 'Automação Local vs Nuvem: Qual a melhor opção?',
    excerpt: 'Entenda por que manter o processamento de dados sensíveis na sua máquina é mais seguro.',
    author: 'Bruno Antonio',
    date: '28 de Abril, 2026',
    category: 'Segurança',
    image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc51?auto=format&fit=crop&q=80&w=800',
  },
  {
    id: 3,
    title: 'Como o DataMaster Pro reduziu custos em 30% na LogTech',
    excerpt: 'Um estudo de caso real sobre a implementação do nosso minerador de dados.',
    author: 'Marketing DM',
    date: '15 de Abril, 2026',
    category: 'Cases',
    image: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=800',
  },
]

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-extrabold text-surface-900 mb-4">Blog & Insights</h1>
          <p className="text-lg text-surface-600">Compartilhando conhecimento para elevar sua produtividade.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {POSTS.map((post) => (
            <article key={post.id} className="bg-white rounded-[2rem] overflow-hidden shadow-sm border border-surface-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col">
              <div className="h-48 overflow-hidden relative">
                <img 
                  src={post.image} 
                  alt={post.title}
                  className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
                />
                <span className="absolute top-4 left-4 bg-primary-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                  {post.category}
                </span>
              </div>
              <div className="p-8 flex-1 flex flex-col">
                <div className="flex items-center gap-4 text-xs text-surface-400 mb-4">
                  <span className="flex items-center gap-1"><User className="w-3 h-3" /> {post.author}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {post.date}</span>
                </div>
                <h2 className="text-xl font-bold text-surface-900 mb-3 group-hover:text-primary-600 transition-colors line-clamp-2">
                  {post.title}
                </h2>
                <p className="text-surface-600 text-sm leading-relaxed mb-6 line-clamp-3">
                  {post.excerpt}
                </p>
                <div className="mt-auto pt-6 border-t border-surface-50">
                  <button className="text-primary-600 font-bold flex items-center gap-2 hover:gap-3 transition-all text-sm uppercase tracking-wide">
                    Ler artigo <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
