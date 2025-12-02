'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';

export default function Search() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [searchText, setSearchText] = useState(searchParams.get('q') || '');
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Update URL after user stops typing (300ms debounce)
  useEffect(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      const currentQ = searchParams.get('q') || '';
      const trimmedSearch = searchText.trim();
      
      // Only update URL if the value actually changed
      if (currentQ !== trimmedSearch) {
        const params = new URLSearchParams(searchParams.toString());
        
        if (trimmedSearch) {
          params.set('q', trimmedSearch);
        } else {
          params.delete('q');
        }

        const queryString = params.toString();
        const newUrl = queryString ? `?${queryString}` : '';
        
        router.push(`/listings${newUrl}`);
      }
    }, 300);

    // Cleanup timer on unmount or when searchText changes
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchText, router, searchParams]);

  return (
    <div className="w-full max-w-2xl">
      <div className="relative">
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search listings..."
          className="w-full px-4 py-3 pr-12 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <svg
          className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </div>
  );
}
