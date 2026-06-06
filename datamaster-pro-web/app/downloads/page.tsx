import { createClient } from "@/lib/supabase/server";
import { CheckCircle, Download, FileText, Monitor } from "lucide-react";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Downloads - DataMaster Pro",
  description: "Baixe o aplicativo DataMaster Pro para Windows",
};

// Revalida a cada 2 hora para não cachear link antigo eternamente
export const revalidate = 7200;

async function getLatestDownload() {
  try {
    const supabase = await createClient();
    const { data, error } = await supabase
      .from("check_updates")
      .select("versao_disponivel, created_at, tamanho_arquivo, changelog, url_download")
      .order("id", { ascending: false })
      .limit(1)
      .single();

    if (error) throw error;
    return data;
  } catch (error) {
    console.error("Erro ao buscar link de download:", error);
    return null;
  }
}

export default async function DownloadsPage() {
  const latestUpdate = await getLatestDownload();

  const downloads = [
    {
      platform: "Windows",
      icon: Monitor,
      version: latestUpdate?.versao_disponivel || "1.0.0",
      date: latestUpdate?.created_at ? new Date(latestUpdate.created_at).toLocaleDateString('pt-BR') : "08/05/2026",
      size: latestUpdate?.tamanho_arquivo || "119 MB",
      requirements: ["Windows 10 ou superior", "4GB RAM", "200MB disco"],
      changelog: latestUpdate?.changelog
        ? latestUpdate.changelog.split(/\\n|\n/).map((line: string) => line.replace(/^#+\s*|^-\s*|^\*\s*/, '').trim()).filter((i: string) => i)
        : [
          "5 ferramentas completas",
          "Modo offline",
          "Segurança total Nos Seus dados",
          "Criptografia de ponta a ponta",
        ],
      downloadUrl: latestUpdate?.url_download || "https://github.com/BrunoTg7/DataMaster-Pro-Upgrade/releases/download/1.4.0/DataMaster.Pro.Setup.v1.1.0.exe",
    },
  ];

  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-surface-900 mb-4">
            Downloads
          </h1>
          <p className="text-lg text-surface-600">
            Baixe o aplicativo DataMaster Pro para usar offline no seu
            computador
          </p>
        </div>

        <div className="space-y-6">
          {downloads.map((download) => (
            <div
              key={download.platform}
              className="bg-white rounded-2xl p-6 shadow-sm border border-surface-200"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center">
                    <download.icon className="w-7 h-7 text-primary-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-surface-900">
                      {download.platform}
                    </h2>
                    <p className="text-surface-500">
                      v{download.version} • {download.size}
                    </p>
                  </div>
                </div>
                {download.downloadUrl ? (
                  <a
                    href={download.downloadUrl}
                    download="DataMaster-Pro-Setup.exe"
                    className="btn-primary flex items-center"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Baixar Instalador
                  </a>
                ) : (
                  <button disabled className="btn-secondary flex items-center opacity-50 cursor-not-allowed">
                    Indisponível
                  </button>
                )}
              </div>

              <div className="grid sm:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-surface-900 mb-3">
                    Requisitos do Sistema
                  </h3>
                  <ul className="space-y-2">
                    {download.requirements.map((req) => (
                      <li
                        key={req}
                        className="flex items-center gap-2 text-sm text-surface-600"
                      >
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-surface-900 mb-3">
                    Notas da Versão ({download.version})
                  </h3>
                  <ul className="space-y-2">
                    {download.changelog.map((item: string, i: number) => (
                      <li
                        key={i}
                        className="flex items-center gap-2 text-sm text-surface-600"
                      >
                        <CheckCircle className="w-4 h-4 text-primary-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 bg-surface-900 rounded-2xl p-6 text-white">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
              <FileText className="w-5 h-5 text-primary-500" />
            </div>
            <div>
              <h3 className="font-bold mb-2">
                Precisa de ajuda com a instalação?
              </h3>
              <p className="text-surface-300 text-sm mb-4">
                Temos guias passo a passo para ajudar você a começar.
              </p>
              <a
                href="/ajuda"
                className="text-primary-400 text-sm font-medium hover:underline"
              >
                Ver guia de instalação →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
