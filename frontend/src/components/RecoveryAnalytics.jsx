import { ArrowDown, ArrowUp, Clock3 } from 'lucide-react'

export default function RecoveryAnalytics({ incidents = [] }) {
  const incident = incidents.find((item) => item.status === 'recovered' && item.after_metrics)
  const before = incident?.before_metrics
  const after = incident?.after_metrics
  const delta = (a, b) => a && b ? Math.round(((a - b) / a) * 100) : 0
  return (
    <section className="panel recovery-panel">
      <header><div><p>CLOSED-LOOP VERIFICATION</p><h2>Before vs after</h2></div><Clock3 size={20}/></header>
      {!incident ? <div className="empty-state tall">Complete a recovery to unlock comparative analytics.</div> : <>
        <div className="compare-grid">
          <div className="before"><small>BEFORE HEALING</small><strong>{before.latency_ms}<em>ms</em></strong><span>Latency</span><strong>{before.packet_loss_percent}<em>%</em></strong><span>Packet loss</span></div>
          <div className="after"><small>AFTER HEALING</small><strong>{after.latency_ms}<em>ms</em></strong><span>Latency</span><strong>{after.packet_loss_percent}<em>%</em></strong><span>Packet loss</span></div>
        </div>
        <div className="improvement"><span><ArrowDown size={14}/>{delta(before.latency_ms, after.latency_ms)}% latency</span><span><ArrowDown size={14}/>{delta(before.packet_loss_percent, after.packet_loss_percent)}% loss</span><span><ArrowUp size={14}/>{Math.round((after.health_score || 0) - (before.health_score || 0))} pts health</span></div>
        <p className="recovery-time">Recovery verified in <b>{incident.recovery_time_seconds}s</b></p>
      </>}
    </section>
  )
}
