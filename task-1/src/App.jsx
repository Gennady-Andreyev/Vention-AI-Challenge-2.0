import { useState, useMemo } from 'react'
import { employees } from './data/mockData'
import { applyFilters } from './utils/leaderboard'
import Filters from './components/Filters'
import Podium from './components/Podium'
import LeaderboardList from './components/LeaderboardList'
import './App.css'

const DEFAULT_FILTERS = { year: 'all', quarter: 'all', category: 'all', search: '' }

export default function App() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [expandedIds, setExpandedIds] = useState(new Set())

  const ranked = useMemo(() => applyFilters(employees, filters), [filters])

  function toggleRow(id) {
    setExpandedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="page">
      <div className="leaderboard-container">
        <header className="page-header">
          <h1 className="page-title">Leaderboard</h1>
          <p className="page-subtitle">Top performers based on contributions and activity</p>
        </header>

        <Filters filters={filters} onChange={setFilters} />

        {ranked.length >= 3 && (
          <Podium ranked={ranked} />
        )}

        <LeaderboardList
          ranked={ranked}
          expandedIds={expandedIds}
          onToggle={toggleRow}
        />
      </div>
    </div>
  )
}
