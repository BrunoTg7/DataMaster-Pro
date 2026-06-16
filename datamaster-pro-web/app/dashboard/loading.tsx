import { Loader2 } from 'lucide-react'

export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="h-10 w-48 bg-surface-200 rounded-lg animate-pulse" />
          <div className="h-5 w-64 bg-surface-200 rounded-lg animate-pulse mt-2" />
        </div>

        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-6 bg-white rounded-[2rem] border border-surface-100">
                  <div className="h-6 w-6 bg-surface-200 rounded animate-pulse mb-3" />
                  <div className="h-8 w-20 bg-surface-200 rounded animate-pulse mb-1" />
                  <div className="h-3 w-24 bg-surface-200 rounded animate-pulse" />
                </div>
              ))}
            </div>

            <div className="bg-white rounded-[2.5rem] p-8 border border-surface-100">
              <div className="h-6 w-40 bg-surface-200 rounded animate-pulse mb-6" />
              <div className="grid sm:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="p-6 rounded-[2.5rem] border border-surface-100">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-14 h-14 bg-surface-200 rounded-2xl animate-pulse" />
                      <div className="flex-1">
                        <div className="h-4 w-28 bg-surface-200 rounded animate-pulse mb-2" />
                        <div className="h-3 w-20 bg-surface-200 rounded animate-pulse" />
                      </div>
                    </div>
                    <div className="h-3 w-full bg-surface-200 rounded animate-pulse mb-2" />
                    <div className="h-3 w-3/4 bg-surface-200 rounded animate-pulse" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-[2.5rem] p-8 border border-surface-100">
              <div className="h-5 w-24 bg-surface-200 rounded animate-pulse mb-6" />
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-surface-50 rounded-2xl mb-2" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
