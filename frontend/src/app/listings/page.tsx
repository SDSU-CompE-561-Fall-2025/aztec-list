'use client';

import Grid from '@/ui/grid';
import Search from '@/ui/search';
import { useSearchParams } from 'next/navigation';
import { useListings } from '@/lib/hooks/useListings';

export default function ListingsPage() {
  const searchParams = useSearchParams();
  const searchQuery = searchParams.get('q') || undefined;
  
  const { data, isLoading, isError, error } = useListings(searchQuery);

  return (
    <div className="container mx-auto px-4 py-8">
      
      {isLoading && (
        <div className="text-center text-gray-600 py-8">
          <p>Loading listings...</p>
        </div>
      )}
      
      {isError && (
        <div className="text-center text-red-600 py-8">
          <p>Error: {error?.message || 'Failed to fetch listings'}</p>
        </div>
      )}
      
      {data && data.items.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <p>No listings found{searchQuery ? ` for "${searchQuery}"` : ''}.</p>
        </div>
      )}
      
      {data && data.items.length > 0 && (
        <>
          <div className="mb-4 text-gray-600">
            <p>Found {data.count} listing{data.count !== 1 ? 's' : ''}{searchQuery ? ` for "${searchQuery}"` : ''}</p>
          </div>
          <Grid listings={data.items} />
        </>
      )}
    </div>
  );
}
