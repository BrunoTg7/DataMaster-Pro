import { Metadata } from 'next'
import { Briefcase, MapPin, Clock, ArrowRight, Star } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Carreiras - DataMaster Pro',
  description: 'Junte-se ao time que está revolucionando a produtividade com dados.',
}

const JOBS = [
  {
    id: 1,
    role: 'Engenheiro de Software Python (Desktop)',
    department: 'Engenharia',
    location: 'Remoto',
    type: 'Full-time',
    salary: 'R$ 12k - 18k',
  },
  {
    id: 2,
    role: 'Frontend Developer (Next.js)',
    department: 'Engenharia',
    location: 'Remoto',
    type: 'Full-time',
    salary: 'R$ 10k - 15k',
  },
  {
    id: 3,
    role: 'Product Designer (UI/UX)',
    department: 'Produto',
    location: 'Remoto',
    type: 'Full-time',
    salary: 'R$ 9k - 14k',
  },
]

export default function CarreirasPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-bold mb-6">
            <Star className="w-4 h-4" /> Estamos contratando!
          </div>
          <h1 className="text-4xl font-extrabold text-surface-900 mb-4">Construa o Futuro com a Gente</h1>
          <p className="text-lg text-surface-600 max-w-2xl mx-auto leading-relaxed">
            Somos uma equipe apaixonada por código, design e eficiência. 
            Se você quer impactar a vida de milhares de profissionais, seu lugar é aqui.
          </p>
        </div>

        <div className="space-y-4">
          {JOBS.map((job) => (
            <div key={job.id} className="group bg-white p-8 rounded-3xl shadow-sm border border-surface-100 hover:shadow-xl hover:border-primary-200 transition-all duration-300 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-surface-900 group-hover:text-primary-600 transition-colors">{job.role}</h3>
                <div className="flex flex-wrap items-center gap-4 text-sm text-surface-500 font-medium">
                  <span className="flex items-center gap-1"><Briefcase className="w-4 h-4" /> {job.department}</span>
                  <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> {job.location}</span>
                  <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> {job.type}</span>
                  <span className="text-primary-600">{job.salary}</span>
                </div>
              </div>
              <a 
                href={`mailto:talentos@datamaster.pro?subject=${encodeURIComponent(`Candidatura: ${job.role} - DataMaster Pro`)}`}
                className="btn-primary group-hover:scale-105 transition-transform px-8 whitespace-nowrap flex items-center justify-center"
              >
                Ver Detalhes
                <ArrowRight className="w-4 h-4 ml-2" />
              </a>
            </div>
          ))}
        </div>

        <div className="mt-20 bg-gradient-to-br from-primary-600 to-primary-800 rounded-[2.5rem] p-12 text-white text-center">
          <h2 className="text-3xl font-bold mb-4">Não encontrou sua vaga?</h2>
          <p className="text-primary-100 mb-8 max-w-xl mx-auto leading-relaxed">
            Sempre buscamos talentos excepcionais. Envie seu portfólio ou LinkedIn e entraremos em contato.
          </p>
          <a href="mailto:talentos@datamaster.pro" className="inline-block px-10 py-4 bg-white text-primary-700 font-bold rounded-2xl hover:bg-primary-50 transition-colors shadow-lg shadow-primary-900/20">
            Envio Espontâneo
          </a>
        </div>
      </div>
    </div>
  )
}
