import { useState } from 'react'
import Painel from './pages/Painel.jsx'
import Visitas from './pages/Visitas.jsx'
import Tipos from './pages/Tipos.jsx'
import Cartoes from './pages/Cartoes.jsx'
import Catraca from './pages/Catraca.jsx'

const ABAS = [
  { id: 'painel', rotulo: 'Painel' },
  { id: 'visitas', rotulo: 'Visitas' },
  { id: 'catraca', rotulo: 'Catraca' },
  { id: 'tipos', rotulo: 'Tipos de visita' },
  { id: 'cartoes', rotulo: 'Cartões' },
]

export default function App() {
  const [aba, setAba] = useState('painel')
  // Incrementado após cada operação: o Painel recarrega os indicadores.
  const [versao, setVersao] = useState(0)
  const mudou = () => setVersao((v) => v + 1)

  return (
    <div className="app">
      <header className="topo">
        <div className="marca">
          <strong>Gestão de visitantes</strong>
          <span className="ficticio">Órgão fictício · dados fictícios</span>
        </div>
        <nav className="abas" role="tablist" aria-label="Seções">
          {ABAS.map((a) => (
            <button
              key={a.id}
              type="button"
              role="tab"
              aria-selected={aba === a.id}
              className={aba === a.id ? 'aba ativa' : 'aba'}
              onClick={() => setAba(a.id)}
            >
              {a.rotulo}
            </button>
          ))}
        </nav>
      </header>

      <main className="conteudo">
        {aba === 'painel' && <Painel versao={versao} />}
        {aba === 'visitas' && <Visitas onMudou={mudou} />}
        {aba === 'catraca' && <Catraca onMudou={mudou} />}
        {aba === 'tipos' && <Tipos onMudou={mudou} />}
        {aba === 'cartoes' && <Cartoes onMudou={mudou} />}
      </main>

      <footer className="rodape" role="contentinfo">
        <strong>Aviso de privacidade.</strong> Os dados são tratados para segurança das pessoas e do patrimônio,
        controle de acesso e registro de atendimento (LGPD, art. 7º, II e III, e art. 23 — base legal proposta, a
        validar pelo encarregado). Não coletamos foto, biometria nem cópia de documento; o documento é devolvido na
        hora e aparece mascarado nas listagens. Encarregado (fictício): encarregado@orgao-ficticio.example.
        <em> Todos os dados deste sistema são fictícios.</em>
      </footer>
    </div>
  )
}
