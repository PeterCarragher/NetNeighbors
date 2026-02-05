import DiscoveryForm from '@/components/DiscoveryForm'

export default function Home() {
  return (
    <main className="min-h-screen p-8 max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          NetNeighbors
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Discover related news domains using CommonCrawl webgraph analysis.
          Find sites that link to or are linked from your target domain.
        </p>
      </div>

      {/* Discovery Form */}
      <DiscoveryForm />

      {/* Footer */}
      <footer className="mt-16 text-center text-gray-500 text-sm">
        <p>
          Powered by{' '}
          <a
            href="https://commoncrawl.org/web-graphs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            CommonCrawl Web Graphs
          </a>
        </p>
      </footer>
    </main>
  )
}
