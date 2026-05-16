import Link from 'next/link'
import { ArrowLeft, Download, FileText, Printer, Maximize2, QrCode } from 'lucide-react'

export default function OrcamentosDemoPage() {
  return (
    <div className="min-h-screen bg-surface-200 flex flex-col font-sans">
      {/* Header/Navbar */}
      <header className="bg-white border-b border-surface-300 sticky top-0 z-10 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="p-2 hover:bg-surface-100 rounded-lg text-surface-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3 border-l border-surface-200 pl-4">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center text-red-600">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-surface-900">Demonstrativo_Orcamento.pdf</h1>
              <p className="text-xs text-surface-500">Preview Exato do DataMaster Pro Desktop</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-surface-100 rounded-lg text-surface-600 transition-colors" title="Imprimir">
            <Printer className="w-5 h-5" />
          </button>
          <button className="p-2 hover:bg-surface-100 rounded-lg text-surface-600 transition-colors" title="Tela Cheia">
            <Maximize2 className="w-5 h-5" />
          </button>
          <div className="w-px h-6 bg-surface-200 mx-2"></div>
          <button className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-bold transition-all shadow-md shadow-primary-500/20">
            <Download className="w-4 h-4" />
            Baixar PDF
          </button>
        </div>
      </header>

      {/* Main Content / PDF Viewer Simulation */}
      <main className="flex-1 overflow-auto p-4 md:p-8 flex justify-center bg-surface-200">
        {/* PDF Page Simulation - A4 Proportions */}
        <div className="bg-white shadow-2xl max-w-[210mm] w-full min-h-[297mm] mx-auto text-[#1e293b] text-[11px] leading-relaxed relative">

          {/* PDF Margins Container (simulating the 8mm margin used in ReportLab) */}
          <div className="p-[10mm] h-full flex flex-col">

            {/* _bloco_header */}
            <div className="flex items-center gap-4 mb-5">
              <img
                src="/favicon.ico"
                alt="DataMaster Pro"
                className="w-40 h-40  object-cover"
              />
              <div className="ml-4 text-[#64748b] text-[11px] flex-1">
                <div className="text-[21px] font-bold text-[#d48214] uppercase tracking-tight w-[48mm]">
                  DATAMASTER PRO
                </div>
                Av. Paulista, 1000 - São Paulo, SP<br />
                Tel: (11) 99999-9999  |  E-mail: contato@datamaster.pro
              </div>
            </div>

            {/* Linha separadora colorida */}
            <div className="h-[2.4px] bg-[#d48214] w-full mb-1"></div>

            {/* _bloco_titulo */}
            <div className="bg-[#f1f5f9] mt-2 mb-4 p-[6.5mm] pb-[6.5mm] border-b-[3.3px] border-[#d48214] flex justify-between items-center">
              <div className="text-[29px] font-bold text-[#1e293b] uppercase">
                ORÇAMENTO
              </div>
              <div className="text-right text-[#64748b] text-[12px] leading-tight">
                N° <span className="font-bold">042</span><br />
                Emissão: 09/05/2026
              </div>
            </div>

            {/* _bloco_destinatario */}
            <div className="mb-6">
              <div className="text-[10px] font-bold text-[#d48214] mb-1">DESTINATÁRIO</div>
              <div className="text-[14.5px] font-bold text-[#1e293b] mb-0.5">JOÃO DA SILVA - ME</div>
              <div className="text-[#64748b] text-[11px] leading-tight space-y-0.5">
                <div>Doc: 12.345.678/0001-90</div>
                <div>Tel: (21) 98888-8888</div>
                <div>E-mail: joao.silva@email.com.br</div>
                <div>End: Rua das Flores, 123, Bairro Centro, Rio de Janeiro - RJ</div>
              </div>
            </div>

            {/* _bloco_itens */}
            <div className="mb-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#d48214] text-white">
                    <th className="py-1.5 px-[6.5mm] font-bold text-[11px] w-[130mm]">DESCRIÇÃO / SERVIÇO</th>
                    <th className="py-1.5 px-[6.5mm] font-bold text-[11px] text-center w-[24mm]">QTD</th>
                    <th className="py-1.5 px-[6.5mm] font-bold text-[11px] text-center w-[44mm]">UNITÁRIO</th>
                    <th className="py-1.5 px-[5mm] font-bold text-[11px] text-right w-[42mm]">TOTAL</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[#e2e8f0]">
                    <td className="py-2 px-[6.5mm] text-[11px]">Consultoria em Automação de Dados</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">10</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">R$ 150,00</td>
                    <td className="py-2 px-[5mm] text-right text-[11px]">R$ 1.500,00</td>
                  </tr>
                  <tr className="bg-[#f1f5f9] border-b border-[#e2e8f0]">
                    <td className="py-2 px-[6.5mm] text-[11px]">Licença DataMaster Pro (Anual)</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">1</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">R$ 359,28</td>
                    <td className="py-2 px-[5mm] text-right text-[11px]">R$ 359,28</td>
                  </tr>
                  <tr className="border-b border-[#e2e8f0]">
                    <td className="py-2 px-[6.5mm] text-[11px]">Treinamento da Equipe (Online)</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">2</td>
                    <td className="py-2 px-[6.5mm] text-center text-[11px]">R$ 200,00</td>
                    <td className="py-2 px-[5mm] text-right text-[11px]">R$ 400,00</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* _bloco_totais */}
            <div className="flex justify-end mb-8">
              <table className="w-[113mm] border-t border-[#e2e8f0]">
                <tbody>
                  <tr>
                    <td className="py-2 text-[12.5px] font-bold text-[#1e293b] text-right w-[69mm]">TOTAL DO ORÇAMENTO</td>
                    <td className="py-2 text-[20px] font-bold text-[#d48214] text-right w-[44mm]">R$ 2.259,28</td>
                  </tr>
                </tbody>
              </table>
            </div>



            {/* _bloco_obs */}
            <div className="mb-6">
              <div className="text-[10px] font-bold text-[#d48214] mb-1">NOTAS E CONDIÇÕES</div>
              <div className="w-[45mm] h-[1px] bg-[#d48214] mb-2"></div>
              <div className="text-[#64748b] text-[10.5px]">
                Este orçamento é válido por 15 dias a partir da data de emissão.<br />
                O pagamento deve ser realizado via PIX ou transferência bancária.<br />
                O serviço será iniciado somente após a confirmação do pagamento integral.
              </div>
            </div>

            {/* _bloco_pagamento */}
            <div className="mb-2">
              <div className="text-[10px] font-bold text-[#d48214] mb-1">DADOS PARA PAGAMENTO</div>
              <div className="w-[45mm] h-[1px] bg-[#d48214] mb-2"></div>

              <div className="bg-[#f1f5f9] border-l-[3.3px] border-[#d48214] py-3 px-[10mm] flex items-center justify-between">
                <div className="text-[#1e293b] text-[12px] leading-relaxed">
                  <span className="font-bold">Chave PIX:</span> 12.345.678/0001-90<br />
                  <span className="font-bold">Banco:</span> 237  |  <span className="font-bold">Agência:</span> 0001  |  <span className="font-bold">Conta:</span> 12345-6
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-[36mm] h-[36mm] bg-white border border-surface-200 flex items-center justify-center p-2 mb-1">
                    <QrCode className="w-full h-full text-surface-900" />
                  </div>
                  <div className="text-[8.5px] text-[#64748b]">Escaneie para pagar</div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  )
}