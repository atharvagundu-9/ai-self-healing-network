import { Activity, Bell, CheckCircle2, Radio, Server, Shield, Sparkles, WifiOff } from 'lucide-react'
import { useState } from 'react'
import AIPanel from './components/AIPanel'
import BackendConsole from './components/BackendConsole'
import DemoControls from './components/DemoControls'
import NetworkTopology from './components/NetworkTopology'
import RecoveryAnalytics from './components/RecoveryAnalytics'
import StatCard from './components/StatCard'
import TelemetryCharts from './components/TelemetryCharts'
import Timeline from './components/Timeline'
import { useNetworkStream } from './hooks/useNetworkStream'

export default function App() {
  const { data, connected, history } = useNetworkStream()
  const [notice, setNotice] = useState(null)
  const status = data?.status || { network_health: 100, active_devices: 8, active_alerts: 0, predicted_failures: 0, successful_recoveries: 0, phase: 'monitoring' }
  const activeDevice = data?.prediction?.device_id
  const notify = (message, error) => { setNotice({ message, error }); setTimeout(() => setNotice(null), 3500) }
  return (
    <div className="app-shell">
      <nav>
        <div className="brand"><div className="brand-mark"><Shield/><i/></div><div><strong>AEGIS <em>NET</em></strong><span>Autonomous Network Defense</span></div></div>
        <div className="nav-center"><span className={connected ? 'connected' : 'disconnected'}><i/>{connected ? 'LIVE STREAM' : 'RECONNECTING'}</span><b>SIMULATION ENVIRONMENT</b></div>
        <div className="nav-right"><span><Radio size={15}/> WS / 1 SEC</span><Bell size={18}/><div className="avatar">AI</div></div>
      </nav>
      <main>
        <header className="hero"><div><span className="eyebrow"><Sparkles size={13}/> PREDICTIVE NETWORK OPERATIONS</span><h1>AI Self-Healing <em>Network</em></h1><p>Real-time telemetry, machine-learning failure prediction, and closed-loop autonomous recovery.</p></div><div className="engine-state"><small>HEALING ENGINE</small><strong><i/> {status.phase.toUpperCase()}</strong><span>Policy guardrails active</span></div></header>
        <section className="stats">
          <StatCard label="Network health" value={status.network_health} suffix="%" icon={Activity} tone={status.network_health < 70 ? 'red' : 'cyan'}/>
          <StatCard label="Active devices" value={`${status.active_devices}/${status.total_devices || 8}`} icon={Server} tone="green"/>
          <StatCard label="Active alerts" value={status.active_alerts} icon={status.active_alerts ? WifiOff : Bell} tone={status.active_alerts ? 'red' : 'green'}/>
          <StatCard label="Predicted failures" value={status.predicted_failures} icon={Sparkles} tone="amber"/>
          <StatCard label="Successful recoveries" value={status.successful_recoveries} icon={CheckCircle2} tone="purple"/>
        </section>
        <div className="dashboard-grid">
          <div className="wide"><NetworkTopology topology={data?.topology} activeDevice={activeDevice} phase={status.phase}/></div>
          <AIPanel prediction={data?.prediction} risk={data?.risk} diagnosis={data?.diagnosis}/>
          <div className="wide"><TelemetryCharts history={history}/></div>
          <DemoControls busy={Boolean(status.active_alerts)} onNotice={notify}/>
          <div className="full"><BackendConsole logs={data?.backend_console} connected={connected}/></div>
          <div className="wide"><Timeline events={data?.events}/></div>
          <RecoveryAnalytics incidents={data?.incidents}/>
        </div>
      </main>
      <footer className="app-footer"><span>AEGIS NET · COLLEGE NETWORK LAB</span><span><i/> SIMULATED TELEMETRY & ACTIONS</span><span>Isolation Forest + Random Forest</span></footer>
      {notice && <div className={`toast ${notice.error ? 'error' : ''}`}>{notice.message}</div>}
    </div>
  )
}
