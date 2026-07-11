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
      .select("versao_disponivel, updated_at, tamanho_arquivo, changelog, url_download")
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
      date: latestUpdate?.updated_at ? new Date(latestUpdate.updated_at).toLocaleDateString('pt-BR') : "08/05/2026",
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
    <div className="min-h-screen bg-surface-50 pt-20 sm:pt-24 pb-10 sm:pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-2xl sm:text-4xl font-bold text-surface-900 mb-3 sm:mb-4">
            Downloads
          </h1>
          <p className="text-sm sm:text-lg text-surface-600">
            Baixe o aplicativo DataMaster Pro para usar offline no seu
            computador
          </p>
        </div>

        <div className="space-y-4 sm:space-y-6">
          {downloads.map((download) => (
            <div
              key={download.platform}
              className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 shadow-sm border border-surface-200"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-5 sm:mb-6">
                <div className="flex items-center gap-3 sm:gap-4">
                  <div className="w-11 h-11 sm:w-14 sm:h-14 bg-primary-100 rounded-xl sm:rounded-2xl flex items-center justify-center">
                    <download.icon className="w-5 h-5 sm:w-7 sm:h-7 text-primary-600" />
                  </div>
                  <div>
                    <h2 className="text-base sm:text-xl font-bold text-surface-900">
                      {download.platform}
                    </h2>
                    <p className="text-surface-500 text-xs sm:text-sm">
                      v{download.version} • {download.size}
                    </p>
                  </div>
                </div>
                {download.downloadUrl ? (
                  <a
                    href={download.downloadUrl}
                    download="DataMaster-Pro-Setup.exe"
                    className="btn-primary flex items-center justify-center text-sm sm:text-base py-2.5 sm:py-3"
                  >
                    <Download className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                    Baixar Instalador
                  </a>
                ) : (
                  <button disabled className="btn-secondary flex items-center justify-center opacity-50 cursor-not-allowed text-sm sm:text-base py-2.5 sm:py-3">
                    Indisponível
                  </button>
                )}
              </div>

              <div className="grid sm:grid-cols-2 gap-4 sm:gap-6">
                <div>
                  <h3 className="font-semibold text-surface-900 mb-2 sm:mb-3 text-sm sm:text-base">
                    Requisitos do Sistema
                  </h3>
                  <ul className="space-y-1.5 sm:space-y-2">
                    {download.requirements.map((req) => (
                      <li
                        key={req}
                        className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-surface-600"
                      >
                        <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-surface-900 mb-2 sm:mb-3 text-sm sm:text-base">
                    Notas da Versão ({download.version})
                  </h3>
                  <ul className="space-y-1.5 sm:space-y-2">
                    {download.changelog.map((item: string, i: number) => (
                      <li
                        key={i}
                        className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-surface-600"
                      >
                        <CheckCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-primary-500 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 sm:mt-12 bg-surface-900 rounded-xl sm:rounded-2xl p-4 sm:p-6 text-white">
          <div className="flex items-start gap-3 sm:gap-4">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-primary-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
            </div>
            <div>
              <h3 className="font-bold mb-1.5 sm:mb-2 text-sm sm:text-base">
                Precisa de ajuda com a instalação?
              </h3>
              <p className="text-surface-300 text-xs sm:text-sm mb-3 sm:mb-4">
                Temos guias passo a passo para ajudar você a começar.
              </p>
              <a
                href="/ajuda"
                className="text-primary-400 text-xs sm:text-sm font-medium hover:underline"
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
