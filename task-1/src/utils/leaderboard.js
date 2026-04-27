import { CATEGORIES } from '../data/mockData'

function getYear(dateStr) {
  return new Date(dateStr).getFullYear().toString()
}

function getQuarter(dateStr) {
  const month = new Date(dateStr).getMonth() + 1
  if (month <= 3) return 'Q1'
  if (month <= 6) return 'Q2'
  if (month <= 9) return 'Q3'
  return 'Q4'
}

export function getAvailableYears(employees) {
  const years = new Set()
  employees.forEach(emp => emp.activities.forEach(a => years.add(getYear(a.date))))
  return Array.from(years).sort().reverse()
}

export function applyFilters(employees, { year, quarter, category, search }) {
  const noDateFilter = year === 'all' && quarter === 'all'
  const noCategoryFilter = category === 'all'
  const noSearchFilter = !search.trim()
  const noFilter = noDateFilter && noCategoryFilter

  return employees
    .map(emp => {
      let acts = emp.activities
      if (year !== 'all') acts = acts.filter(a => getYear(a.date) === year)
      if (quarter !== 'all') acts = acts.filter(a => getQuarter(a.date) === quarter)
      if (!noCategoryFilter) acts = acts.filter(a => a.category === category)
      const total = acts.reduce((sum, a) => sum + a.points, 0)
      return { ...emp, filteredActivities: acts, filteredTotal: total }
    })
    .filter(emp => {
      const hasPoints = noFilter || emp.filteredTotal > 0
      const matchesSearch = noSearchFilter || emp.name.toLowerCase().includes(search.trim().toLowerCase())
      return hasPoints && matchesSearch
    })
    .sort((a, b) => b.filteredTotal - a.filteredTotal)
    .map((emp, i) => ({ ...emp, rank: i + 1 }))
}

export function getCategoryCountsForRow(activities) {
  const counts = {}
  activities.forEach(a => {
    counts[a.category] = (counts[a.category] || 0) + 1
  })
  return counts
}

export const CATEGORY_ORDER = [
  CATEGORIES.PUBLIC_SPEAKING,
  CATEGORIES.EDUCATION,
  CATEGORIES.UNIVERSITY,
]
