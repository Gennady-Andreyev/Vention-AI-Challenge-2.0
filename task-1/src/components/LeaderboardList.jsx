import LeaderboardRow from './LeaderboardRow'
import './LeaderboardList.css'

export default function LeaderboardList({ ranked, expandedIds, onToggle }) {
  if (ranked.length === 0) {
    return <div className="lb-empty">No results match the current filters.</div>
  }

  return (
    <div className="lb-list">
      {ranked.map(person => (
        <LeaderboardRow
          key={person.id}
          person={person}
          expanded={expandedIds.has(person.id)}
          onToggle={() => onToggle(person.id)}
        />
      ))}
    </div>
  )
}
