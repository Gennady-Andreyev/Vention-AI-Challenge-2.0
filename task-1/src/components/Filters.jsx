import { Search, ChevronDown } from 'lucide-react'
import './Filters.css'

const years = ['2024', '2025']
const quarters = ['Q1', 'Q2', 'Q3', 'Q4']
const categories = ['Education', 'Public Speaking', 'University Partnership']

export default function Filters({ filters, onChange }) {
  return (
    <div className="filters-bar">
      <div className="filter-select-wrap">
        <select
          value={filters.year}
          onChange={e => onChange({ ...filters, year: e.target.value })}
          className="filter-select"
        >
          <option value="all">All Years</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <ChevronDown size={14} className="filter-chevron" />
      </div>

      <div className="filter-select-wrap">
        <select
          value={filters.quarter}
          onChange={e => onChange({ ...filters, quarter: e.target.value })}
          className="filter-select"
        >
          <option value="all">All Quarters</option>
          {quarters.map(q => <option key={q} value={q}>{q}</option>)}
        </select>
        <ChevronDown size={14} className="filter-chevron" />
      </div>

      <div className="filter-select-wrap">
        <select
          value={filters.category}
          onChange={e => onChange({ ...filters, category: e.target.value })}
          className="filter-select"
        >
          <option value="all">All Categories</option>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <ChevronDown size={14} className="filter-chevron" />
      </div>

      <div className="filter-search-wrap">
        <Search size={15} className="search-icon" />
        <input
          type="text"
          placeholder="Search employee..."
          value={filters.search}
          onChange={e => onChange({ ...filters, search: e.target.value })}
          className="filter-search"
        />
      </div>
    </div>
  )
}
