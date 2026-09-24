import { Activity, Gauge, RadioTower, RefreshCw, Router, Unplug, Zap } from 'lucide-react'
import { post } from '../services/api'

const controls = [
  ['congestion', 'Inject congestion', Gauge],
  ['link_failure', 'Cause link failure', Unplug],
  ['device_overload', 'Overload router', Router],
  ['traffic_spike', 'Traffic spike', RadioTower],
]

export default function DemoControls({ busy, onNotice }) {
  const inject = async (fault_type) => {
    try {
      const result = await post('/api/fault/inject', { fault_type, device_id: 'r1' })
      onNotice(result.message, false)
    } catch (error) { onNotice(error.message, true) }
  }
  const restore = async () => {
    try { const result = await post('/api/fault/restore'); onNotice(result.message, false) }
    catch (error) { onNotice(error.message, true) }
  }
  return (
    <section className="panel demo-panel">
      <header><div><p>CLASSROOM SCENARIO CONTROLS</p><h2>Demo mode</h2></div><span className="sim-chip"><Zap size={12}/> SIMULATED</span></header>
      <p className="demo-copy">Inject a controlled fault and watch the complete detect → diagnose → heal → verify sequence.</p>
      <div className="demo-buttons">
        {controls.map(([type, label, Icon]) => <button key={type} disabled={busy} onClick={() => inject(type)}><Icon size={17}/><span>{label}</span><Activity size={13}/></button>)}
        <button className="restore" onClick={restore}><RefreshCw size={17}/><span>Restore network</span></button>
      </div>
    </section>
  )
}

