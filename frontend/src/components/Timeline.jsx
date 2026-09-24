import { Check, CircleAlert, Cpu, Route, Search, ShieldCheck } from 'lucide-react'

const iconFor = (type) => {
  if (type?.includes('verified')) return Check
  if (type?.includes('healing')) return Route
  if (type?.includes('root')) return Search
  if (type?.includes('predicted')) return Cpu
  if (type?.includes('anomaly') || type?.includes('fault')) return CircleAlert
  return ShieldCheck
}

export default function Timeline({ events = [] }) {
  return (
    <section className="panel timeline-panel">
      <header><div><p>INCIDENT LOG</p><h2>Self-healing timeline</h2></div><span>{events.length} EVENTS</span></header>
      <div className="timeline">
        {events.length === 0 && <div className="empty-state">Waiting for an incident. Use Demo Mode to inject one.</div>}
        {events.slice(0, 9).map((event) => {
          const Icon = iconFor(event.event_type)
          return <article key={event.id} className={event.level.toLowerCase()}><div className="timeline-icon"><Icon size={14}/></div><div><time>{new Date(event.timestamp).toLocaleTimeString()}</time><strong>{event.message}</strong><small>{event.event_type.replaceAll('_', ' ').toUpperCase()}</small></div></article>
        })}
      </div>
    </section>
  )
}

