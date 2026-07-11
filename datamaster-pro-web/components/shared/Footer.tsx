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
    <footer role="contentinfo" className="bg-surface-900 text-surface-300 border-t border-surface-800">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16">
          <nav aria-label="Links do rodape">
            <div className="grid grid-cols-3 md:grid-cols-5 gap-4 sm:gap-8 lg:gap-12">
          <div className="col-span-3 md:col-span-2">
            <Link href="/" className="flex items-center gap-2 mb-3 sm:mb-4">
              <img
                src="/favicon.ico"
                alt="DataMaster Pro"
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg shadow-lg object-cover"
              />
              <span className="text-base sm:text-lg font-bold text-white">
                DataMaster<span className="text-primary-500">Pro</span>
              </span>
            </Link>
            <p className="text-surface-400 text-xs sm:text-sm mb-4 sm:mb-6 max-w-xs">
              A solução definitiva para produtividade com planilhas Excel.
              Automatize tarefas repetitivas e foque no que realmente importa.
            </p>
            <div className="flex gap-3 sm:gap-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-8 h-8 sm:w-10 sm:h-10 bg-surface-800 rounded-lg flex items-center justify-center hover:bg-surface-700 hover:text-primary-500 transition-colors"
                  aria-label={social.label}
                >
                  <social.icon className="w-4 h-4 sm:w-5 sm:h-5" />
                </a>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-2.5 sm:mb-4 text-xs sm:text-base">Produto</h3>
            <ul className="space-y-1.5 sm:space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-[10px] sm:text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-2.5 sm:mb-4 text-xs sm:text-base">Empresa</h3>
            <ul className="space-y-1.5 sm:space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-[10px] sm:text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-2.5 sm:mb-4 text-xs sm:text-base">Legal</h3>
            <ul className="space-y-1.5 sm:space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-[10px] sm:text-sm text-surface-400 hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        </nav>

        <div className="mt-8 sm:mt-12 pt-6 sm:pt-8 border-t border-surface-800 flex flex-col md:flex-row justify-between items-center gap-3 sm:gap-4">
          <p className="text-xs sm:text-sm text-surface-500">
            © {new Date().getFullYear()} DataMaster Pro. Todos os direitos reservados.
          </p>
          <p className="text-xs sm:text-sm text-surface-500">
            Feito com <span className="text-primary-500">♥</span> no Brasil
          </p>
        </div>
      </div>
    </footer>
  )
}