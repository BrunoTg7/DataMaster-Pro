import { Footer } from "@/components/shared/Footer";
import { Header } from "@/components/shared/Header";
import { ConsentBanner } from "@/components/shared/ConsentBanner";
import { ClientProviders } from "@/components/shared/ClientProviders";
import { ThemeInitializer } from "@/hooks/ThemeInitializer";
import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://datamasterpro.com.br"),
  title: {
    default: "DataMaster Pro - Ferramentas Profissionais para Excel",
    template: "%s | DataMaster Pro",
  },
  description:
    "Automatize tarefas repetitivas no Excel com 5 ferramentas poderosas: Consolidador, Categorizador, Orçamentos, Minerador e Conciliador. Economize 20h/mês.",
  keywords: [
    "excel",
    "planilhas",
    "automação",
    "produtividade",
    "consolidador",
    "categorizador",
    "orcamentos",
    "minerador",
    "conciliador",
  ],
  authors: [{ name: "DataMaster Team" }],
  creator: "DataMaster",
  publisher: "DataMaster",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: "https://datamasterpro.com.br",
    siteName: "DataMaster Pro",
    title: "DataMaster Pro - Ferramentas Profissionais para Excel",
    description:
      "Automatize tarefas repetitivas no Excel com 5 ferramentas poderosas. Consolidador, Categorizador, Orçamentos, Minerador e Conciliador.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "DataMaster Pro",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "DataMaster Pro - Ferramentas Profissionais para Excel",
    description:
      "Automatize tarefas repetitivas no Excel. 5 ferramentas poderosas.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: [
      { url: "/favicon.ico", type: "image/x-icon" },
      { url: "/favicon.ico", sizes: "16x16" },
      { url: "/favicon.ico", sizes: "32x32" },
    ],
    apple: {
      url: "/favicon.ico",
    },
  },
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen flex flex-col">
        <ClientProviders>
          <ThemeInitializer />
          <a href="#main-content" className="skip-link">Pular para o conteudo principal</a>
          <Header />
          <main id="main-content" role="main" className="flex-1">{children}</main>
          <Footer />
          <ConsentBanner />
        </ClientProviders>
      </body>
    </html>
  );
}
