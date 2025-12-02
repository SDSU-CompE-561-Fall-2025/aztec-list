import Grid from '@/ui/grid';
import Search from '@/ui/search';
import { searchListings } from '@/lib/api';
import { ListingSummary } from '@/lib/types';

interface ListingsPageProps {
  searchParams: Promise<{
    q?: string;
  }>;
}

export default async function ListingsPage({ searchParams }: ListingsPageProps) {
  const params = await searchParams;
  const searchQuery = params.q;
  
  // Fetch listings from API
  let listings: ListingSummary[] = [];
  let error: string | null = null;
  
  try {
    const response = await searchListings(searchQuery);
    listings = response.items;
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to fetch listings';
    console.error('Error fetching listings:', err);
  }

  return (
    <div className="container mx-auto px-4 py-8">
      
      {error ? (
        <div className="text-center text-red-600 py-8">
          <p>Error: {error}</p>
        </div>
      ) : listings.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No listings found{searchQuery ? ` for "${searchQuery}"` : ''}.</p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-gray-600">
            <p>Found {listings.length} listing{listings.length !== 1 ? 's' : ''}{searchQuery ? ` for "${searchQuery}"` : ''}</p>
          </div>
          <Grid listings={listings} />
        </>
      )}
    </div>
  );
}
