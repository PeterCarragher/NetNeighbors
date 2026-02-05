'use client'

import { useState } from 'react'

interface DiscoveredDomain {
  domain: string
  count: number
}

interface DiscoveryResult {
  jobId: string
  status: string
  domain: string
  direction: string
  threshold: number
  results: DiscoveredDomain[]
  error?: string
  totalFound: number
  processingTimeMs: number
}

export default function DiscoveryForm() {
  const [domain, setDomain] = useState('')
  const [threshold, setThreshold] = useState(2)
  const [direction, setDirection] = useState<'outgoing' | 'incoming'>('outgoing')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DiscoveryResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, threshold, direction }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Discovery request failed')
      }

      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const exportCsv = () => {
    if (!result?.results) return

    const headers = ['Domain', 'Link Count']
    const rows = result.results.map((r) => [r.domain, r.count.toString()])
    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.domain}-${result.direction}-neighbors.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-8">
      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Domain Input */}
          <div className="md:col-span-2">
            <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
              Domain
            </label>
            <input
              type="text"
              id="domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Direction Select */}
          <div>
            <label htmlFor="direction" className="block text-sm font-medium text-gray-700 mb-1">
              Direction
            </label>
            <select
              id="direction"
              value={direction}
              onChange={(e) => setDirection(e.target.value as 'outgoing' | 'incoming')}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="outgoing">Outgoing (links to)</option>
              <option value="incoming">Incoming (links from)</option>
            </select>
          </div>

          {/* Threshold Input */}
          <div>
            <label htmlFor="threshold" className="block text-sm font-medium text-gray-700 mb-1">
              Min Links
            </label>
            <input
              type="number"
              id="threshold"
              value={threshold}
              onChange={(e) => setThreshold(parseInt(e.target.value) || 1)}
              min={1}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-4">
          <button
            type="submit"
            disabled={loading || !domain}
            className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Discovering...' : 'Discover Neighbors'}
          </button>
        </div>
      </form>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Results */}
      {result && result.status === 'completed' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Results Header */}
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Results for {result.domain}
              </h2>
              <p className="text-sm text-gray-500">
                Found {result.totalFound} domains ({result.direction} links, min {result.threshold})
                {' '}&bull;{' '}
                Processed in {result.processingTimeMs}ms
              </p>
            </div>
            {result.results.length > 0 && (
              <button
                onClick={exportCsv}
                className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                Export CSV
              </button>
            )}
          </div>

          {/* Results Table */}
          {result.results.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Domain
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Link Count
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.results.slice(0, 100).map((item, index) => (
                    <tr key={item.domain} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <a
                          href={`https://${item.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          {item.domain}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        {item.count.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.results.length > 100 && (
                <p className="text-sm text-gray-500 mt-2 text-center">
                  Showing top 100 of {result.results.length} results. Export CSV for full list.
                </p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              No domains found matching your criteria.
            </p>
          )}
        </div>
      )}

      {/* Error Result */}
      {result && result.status === 'error' && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {result.error || 'An error occurred during discovery'}
        </div>
      )}
    </div>
  )
}
