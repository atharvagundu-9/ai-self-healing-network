import { TerminalSquare } from 'lucide-react'
import { useEffect, useRef } from 'react'

export default function BackendConsole({ logs = [], connected }) {
  const viewport = useRef(null)

  useEffect(() => {
    if (viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight
  }, [logs])

  return (
    <section className="panel backend-console-panel">
      <header>
        <div><p>FASTAPI · LIVE SERVER OUTPUT</p><h2>Backend activity console</h2></div>
        <span className={connected ? 'console-connected' : 'console-disconnected'}><i />{connected ? 'STREAMING' : 'OFFLINE'}</span>
      </header>
      <div className="console-toolbar"><TerminalSquare size={14}/><span>AEGIS BACKEND</span><b>{logs.length} buffered messages</b></div>
      <div className="backend-console" ref={viewport}>
        {logs.length === 0 && <div className="console-empty"><span>$</span> Waiting for backend activity. Inject a fault from Demo Mode.</div>}
        {logs.map((entry, index) => (
          <div className={`console-line level-${entry.level.toLowerCase()}`} key={`${entry.timestamp}-${index}`}>
            <time>{new Date(entry.timestamp).toLocaleTimeString([], { hour12: false })}</time>
            <span className="console-level">{entry.level}</span>
            <strong>[AEGIS][{entry.category}]</strong>
            <code>{entry.message}</code>
          </div>
        ))}
      </div>
    </section>
  )
}
