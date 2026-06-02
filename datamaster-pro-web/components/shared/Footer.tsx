import { Github, Mail, Twitter } from 'lucide-react'
import Link from 'next/link'

const footerLinks = {
  product: [
    { label: 'Planos', href: '/planos' },
    { label: 'Downloads', href: '/downloads' },
    { label: 'Funcionalidades', href: '/#features' },
  ],
  company: [
    { label: 'Sobre nós', href: '/sobre' },

  ],
  support: [
    { label: 'Central de Ajuda', href: '/ajuda' },
    { label: 'Contato', href: '/contato' },
    { label: 'Status', href: '/status' },
  ],
  legal: [
    { label: 'Privacidade', href: '/privacidade' },
    { label: 'Termos', href: '/termos' },
    { label: 'LGPD', href: '/lgpd' },
  ],
}

const socialLinks = [
  { icon: Github, href: 'https://github.com', label: 'GitHub' },
  { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
  { icon: Mail, href: 'mailto:suporte@datamaster.pro', label: 'Email' },
]

export function Footer() {
  return (
    <footer className="bg-surface-900 text-surface-300">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <img
                src="/favicon.ico"
                alt="DataMaster Pro"
                className="w-8 h-8 rounded-lg shadow-lg object-cover"
              />
              <span className="text-lg font-bold text-white">
                DataMaster<span className="text-primary-500">Pro</span>
              </span>
            </Link>
            <p className="text-surface-400 text-sm mb-6 max-w-xs">
              A solução definitiva para produtividade com planilhas Excel.
              Automatize tarefas repetitivas e foque no que realmente importa.
            </p>
            <div className="flex gap-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 bg-surface-800 rounded-lg flex items-center justify-center hover:bg-surface-700 hover:text-primary-500 transition-colors"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Produto</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Empresa</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-surface-800 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-surface-500">
            © {new Date().getFullYear()} DataMaster Pro. Todos os direitos reservados.
          </p>
          <p className="text-sm text-surface-500">
            Feito com <span className="text-primary-500">♥</span> no Brasil
          </p>
        </div>
      </div>
    </footer>
  )
}