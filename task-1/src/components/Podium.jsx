import { Star } from 'lucide-react'
import './Podium.css'

function getInitials(name) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

function PodiumCard({ person, medalClass }) {
  if (!person) return <div className={`podium-card podium-empty ${medalClass}`} />
  const initials = getInitials(person.name)
  return (
    <div className={`podium-card ${medalClass}`}>
      <div className="podium-avatar-wrap">
        <div className="podium-avatar">{initials}</div>
        <div className={`podium-rank-badge ${medalClass}-badge`}>{person.rank}</div>
      </div>
      <div className="podium-name">{person.name}</div>
      <div className="podium-meta">{person.title} ({person.unit})</div>
      <div className="podium-score">
        <Star size={14} className="podium-star" fill="currentColor" />
        {person.filteredTotal}
      </div>
    </div>
  )
}

export default function Podium({ ranked }) {
  const first = ranked[0]
  const second = ranked[1]
  const third = ranked[2]

  return (
    <div className="podium-section">
      <div className="podium-cards-row">
        <div className="podium-slot podium-slot-2">
          <PodiumCard person={second} medalClass="silver" />
          <div className="podium-platform podium-platform-2"><span>2</span></div>
        </div>
        <div className="podium-slot podium-slot-1">
          <PodiumCard person={first} medalClass="gold" />
          <div className="podium-platform podium-platform-1"><span>1</span></div>
        </div>
        <div className="podium-slot podium-slot-3">
          <PodiumCard person={third} medalClass="bronze" />
          <div className="podium-platform podium-platform-3"><span>3</span></div>
        </div>
      </div>
    </div>
  )
}
