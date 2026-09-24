import { BrainCircuit, ShieldCheck } from 'lucide-react'

const pretty = (value = '') => value.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export default function AIPanel({ prediction, risk, diagnosis }) {
  const failure = prediction?.predicted_failure || 'normal'
  const confidence = Math.round((prediction?.confidence || 0) * 100)
  const metrics = diagnosis?.relevant_metrics || {}
  return (
    <section className="panel ai-panel">
      <header><div><p>AI NETWORK ANALYSIS</p><h2>Predictive intelligence</h2></div><BrainCircuit size={22}/></header>
      <div className={`risk-banner risk-${(risk?.level || 'low').toLowerCase()}`}>
        <div><small>FAILURE RISK</small><strong>{risk?.level || 'LOW'}</strong></div>
        <div className="confidence-ring" style={{'--confidence': `${confidence * 3.6}deg`}}><span>{confidence}%</span></div>
      </div>
      <dl className="analysis-list">
        <div><dt>Device</dt><dd>{prediction?.device_id?.toUpperCase() || 'R1'} · Edge Router</dd></div>
        <div><dt>Predicted issue</dt><dd className={failure === 'normal' ? 'good' : 'warn'}>{pretty(failure)}</dd></div>
        <div><dt>Probable cause</dt><dd>{diagnosis?.probable_cause || 'No fault signature detected.'}</dd></div>
      </dl>
      <div className="evidence">
        <small>EVIDENCE</small>
        {Object.keys(metrics).length ? Object.entries(metrics).slice(0,4).map(([key, value]) => <span key={key}>{pretty(key)} <b>{value}</b></span>) : <p>Telemetry remains inside the learned baseline.</p>}
      </div>
      <div className="recommendation"><ShieldCheck size={18}/><div><small>RISK FORECAST</small><p>{risk?.message || 'Collecting recent telemetry trends.'}</p></div></div>
    </section>
  )
}

