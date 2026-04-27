import './Podium.css'

const PASTEL_PALETTE = ['#60A5FA', '#34D399', '#F472B6', '#FBBF24', '#A78BFA']

function getInitials(name) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

function pickColor(initials) {
  let hash = 0
  for (let i = 0; i < initials.length; i++) {
    hash = (hash << 5) - hash + initials.charCodeAt(i)
    hash |= 0
  }
  return PASTEL_PALETTE[Math.abs(hash) % PASTEL_PALETTE.length]
}

function StarIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2 L14.7 8.6 L21.8 9.2 L16.4 13.9 L18.1 20.9 L12 17.3 L5.9 20.9 L7.6 13.9 L2.2 9.2 L9.3 8.6 Z" />
    </svg>
  )
}

function PodiumColumn({ person, medal, rank }) {
  if (!person) return <div className={`podium-col podium-col--${medal}`} />
  const initials = getInitials(person.name)
  const color = pickColor(initials)

  return (
    <div className={`podium-col podium-col--${medal}`}>
      <div className="podium-userblock">
        <div className="podium-avatar-wrap">
          <div
            className={`podium-avatar podium-avatar--${medal}`}
            style={{ background: color }}
          >
            {initials}
          </div>
          <div className={`podium-badge podium-badge--${medal}`}>{rank}</div>
        </div>
        <div className="podium-name">{person.name}</div>
        <div className="podium-role">{person.title} ({person.unit})</div>
        <div className="podium-score">
          <StarIcon size={14} />
          <span>{person.filteredTotal}</span>
        </div>
      </div>
      <div className={`podium-block podium-block--${medal}`}>
        <span>{rank}</span>
      </div>
    </div>
  )
}

export default function Podium({ entries }) {
  const first = entries.find(e => e?.rank === 1)
  const second = entries.find(e => e?.rank === 2)
  const third = entries.find(e => e?.rank === 3)

  return (
    <div className="podium">
      <PodiumColumn person={second} medal="silver" rank={2} />
      <PodiumColumn person={first} medal="gold" rank={1} />
      <PodiumColumn person={third} medal="bronze" rank={3} />
    </div>
  )
}
