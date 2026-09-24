import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const CustomTooltip = ({ active, payload, label }) => active && payload?.length ? (
  <div className="chart-tooltip"><small>{label}</small>{payload.map((item) => <div key={item.name}><i style={{background:item.color}} />{item.name}: <b>{item.value}</b></div>)}</div>
) : null

export default function TelemetryCharts({ history }) {
  return (
    <section className="panel charts-panel">
      <header><div><p>STREAMING TELEMETRY · ROUTER R1</p><h2>Performance signals</h2></div><span className="window-chip">LAST 40 SECONDS</span></header>
      <div className="chart-grid">
        <div className="chart"><label>Latency <em>ms</em></label><ResponsiveContainer width="100%" height={150}><AreaChart data={history}><defs><linearGradient id="cyan" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#18d9e8" stopOpacity={.35}/><stop offset="100%" stopColor="#18d9e8" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#17313b" vertical={false}/><XAxis dataKey="time" hide/><YAxis width={30} tick={{fill:'#668691',fontSize:10}}/><Tooltip content={<CustomTooltip/>}/><Area isAnimationActive={false} name="Latency" type="monotone" dataKey="latency" stroke="#18d9e8" fill="url(#cyan)" strokeWidth={2}/></AreaChart></ResponsiveContainer></div>
        <div className="chart"><label>Utilization <em>%</em></label><ResponsiveContainer width="100%" height={150}><AreaChart data={history}><defs><linearGradient id="amber" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ffb84c" stopOpacity={.35}/><stop offset="100%" stopColor="#ffb84c" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#17313b" vertical={false}/><XAxis dataKey="time" hide/><YAxis domain={[0,100]} width={30} tick={{fill:'#668691',fontSize:10}}/><Tooltip content={<CustomTooltip/>}/><Area isAnimationActive={false} name="Bandwidth" type="monotone" dataKey="bandwidth" stroke="#ffb84c" fill="url(#amber)" strokeWidth={2}/><Line isAnimationActive={false} name="CPU" type="monotone" dataKey="cpu" stroke="#9c7cff" dot={false}/></AreaChart></ResponsiveContainer></div>
      </div>
      <div className="chart-legend"><span><i className="cyan"/>Latency</span><span><i className="amber"/>Bandwidth</span><span><i className="purple"/>CPU</span><span><i className="red"/>Packet loss</span></div>
    </section>
  )
}
