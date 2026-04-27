import { GraduationCap, Presentation, Smile, Star, ChevronDown, ChevronUp } from 'lucide-react'
import { CATEGORIES } from '../data/mockData'
import { getCategoryCountsForRow, CATEGORY_ORDER } from '../utils/leaderboard'
import './LeaderboardRow.css'

function getInitials(name) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

const CATEGORY_ICONS = {
  [CATEGORIES.PUBLIC_SPEAKING]: Presentation,
  [CATEGORIES.EDUCATION]: GraduationCap,
  [CATEGORIES.UNIVERSITY]: Smile,
}

const CATEGORY_PILL_CLASS = {
  [CATEGORIES.EDUCATION]: 'pill-education',
  [CATEGORIES.PUBLIC_SPEAKING]: 'pill-speaking',
  [CATEGORIES.UNIVERSITY]: 'pill-university',
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, '-')
}

export default function LeaderboardRow({ person, expanded, onToggle }) {
  const { rank, name, title, unit, filteredActivities, filteredTotal } = person
  const counts = getCategoryCountsForRow(filteredActivities)
  const rankClass = rank === 1 ? 'rank-gold' : rank === 2 ? 'rank-silver' : rank === 3 ? 'rank-bronze' : ''

  return (
    <div className={`lb-row ${expanded ? 'lb-row--expanded' : ''}`}>
      <div className="lb-row-header" onClick={onToggle}>
        <div className="lb-rank">
          <span className={`rank-num ${rankClass}`}>{rank}</span>
        </div>
        <div className="lb-avatar">{getInitials(name)}</div>
        <div className="lb-info">
          <div className="lb-name">{name}</div>
          <div className="lb-meta">{title} ({unit})</div>
        </div>
        <div className="lb-cats">
          {CATEGORY_ORDER.map(cat => {
            const count = counts[cat]
            if (!count) return null
            const Icon = CATEGORY_ICONS[cat]
            return (
              <div key={cat} className="lb-cat-item" title={cat}>
                <Icon size={20} className="lb-cat-icon" />
                <span>{count}</span>
              </div>
            )
          })}
        </div>
        <div className="lb-total">
          <div className="lb-total-label">TOTAL</div>
          <div className="lb-total-score">
            <Star size={20} fill="currentColor" className="lb-star" />
            <span>{filteredTotal}</span>
          </div>
        </div>
        <button className="lb-toggle" aria-label="toggle">
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {expanded && (
        <div className="lb-activities">
          <div className="lb-activities-title">RECENT ACTIVITY</div>
          <table className="activity-table">
            <thead>
              <tr>
                <th>ACTIVITY</th>
                <th>CATEGORY</th>
                <th>DATE</th>
                <th className="text-right">POINTS</th>
              </tr>
            </thead>
            <tbody>
              {filteredActivities.map(act => (
                <tr key={act.id}>
                  <td className="act-name">{act.name}</td>
                  <td>
                    <span className={`cat-pill ${CATEGORY_PILL_CLASS[act.category]}`}>
                      {act.category}
                    </span>
                  </td>
                  <td className="act-date">{formatDate(act.date)}</td>
                  <td className="act-points">+{act.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
