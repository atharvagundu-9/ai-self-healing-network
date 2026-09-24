export default function StatCard({ label, value, suffix = '', tone = 'cyan', icon: Icon }) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <div className="stat-icon"><Icon size={18} /></div>
      <div>
        <span>{label}</span>
        <strong>{value}{suffix}</strong>
      </div>
      <i />
    </div>
  )
}

