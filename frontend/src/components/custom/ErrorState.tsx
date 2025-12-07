interface ErrorStateProps {
  error: Error;
  showHero?: boolean;
}

export function ErrorState({ error, showHero = false }: ErrorStateProps) {
  const isNetworkError = error.message.includes("fetch");

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Optional Hero Section */}
        {showHero && (
          <div className="mb-12 text-center">
            <h1 className="text-4xl font-bold text-white mb-4">
              Welcome to <span className="text-purple-500">AztecList</span> Campus
            </h1>
            <p className="text-gray-400 text-lg">
              Buy and sell items on campus. Find great deals from fellow students.
            </p>
          </div>
        )}

        {/* Offline State */}
        <div className="flex flex-col items-center justify-center py-20 px-4">
          <div className="text-center max-w-md">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gray-100 mb-2">
              {isNetworkError ? "Unable to Connect" : "Something Went Wrong"}
            </h2>
            <p className="text-gray-400 text-sm mb-6">
              {isNetworkError
                ? "The marketplace is currently offline. Please check back soon."
                : error.message}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
