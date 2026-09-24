import { Cloud, Database, Laptop, Router, Server, Waypoints } from 'lucide-react'

const fallback = [
  { id: 'r1', name: 'Edge Router R1', type: 'router', x: 50, y: 12, status: 'healthy' },
  { id: 'r2', name: 'Backup Router R2', type: 'router', x: 78, y: 28, status: 'healthy' },
  { id: 'core1', name: 'Core Switch', type: 'core_switch', x: 50, y: 36, status: 'healthy' },
  { id: 'sw1', name: 'Access Switch A', type: 'access_switch', x: 25, y: 58, status: 'healthy' },
  { id: 'sw2', name: 'Access Switch B', type: 'access_switch', x: 70, y: 58, status: 'healthy' },
  { id: 'app1', name: 'Application Server', type: 'server', x: 58, y: 82, status: 'healthy' },
  { id: 'db1', name: 'Database Server', type: 'database', x: 83, y: 82, status: 'healthy' },
  { id: 'client1', name: 'Client Lab', type: 'client', x: 15, y: 82, status: 'healthy' },
]
const fallbackLinks = [['internet','r1'],['internet','r2'],['r1','core1'],['r2','core1'],['core1','sw1'],['core1','sw2'],['sw1','client1'],['sw2','app1'],['sw2','db1']]
const icons = { router: Router, core_switch: Waypoints, access_switch: Waypoints, server: Server, database: Database, client: Laptop }

export default function NetworkTopology({ topology, activeDevice, phase }) {
  const devices = topology?.devices || fallback
  const links = topology?.links?.map((l) => [l.source, l.target]) || fallbackLinks
  const nodes = [{ id: 'internet', name: 'Internet', x: 22, y: 12, status: 'healthy', type: 'internet' }, ...devices]
  const byId = Object.fromEntries(nodes.map((node) => [node.id, node]))
  return (
    <section className="panel topology-panel">
      <header><div><p>LIVE NETWORK MAP</p><h2>Network topology</h2></div><span className="live-chip"><b /> PACKET FLOW</span></header>
      <div className="topology">
        <svg className="links" viewBox="0 0 100 100" preserveAspectRatio="none">
          {links.map(([a, b]) => {
            const source = byId[a], target = byId[b]
            const affected = activeDevice && (a === activeDevice || b === activeDevice)
            return <line key={`${a}-${b}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} className={affected ? `affected ${phase}` : ''} />
          })}
        </svg>
        {nodes.map((node) => {
          const Icon = node.type === 'internet' ? Cloud : (icons[node.type] || Server)
          const active = node.id === activeDevice
          return (
            <div key={node.id} className={`node ${node.status} ${active ? 'active' : ''}`} style={{ left: `${node.x}%`, top: `${node.y}%` }}>
              <div className="node-orbit"><Icon size={19} /></div>
              <span>{node.name}</span><small>{node.status === 'healthy' ? 'ONLINE' : node.status.toUpperCase()}</small>
            </div>
          )
        })}
      </div>
      <footer className="legend"><span><i className="healthy"/>Healthy</span><span><i className="warning"/>Warning</span><span><i className="critical"/>Failure</span><span><i className="healing"/>Healing</span></footer>
    </section>
  )
}

