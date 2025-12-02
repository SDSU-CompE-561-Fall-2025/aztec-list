import { ListingSummary } from "@/lib/types";

interface CardProps {
  listing: ListingSummary;
}

export default function Card({ listing }: CardProps) {
  const formattedPrice = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(listing.price);

  return (
    <div className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="bg-gray-200 h-48 flex items-center justify-center">
        {listing.thumbnail_url ? (
          <img
            src={listing.thumbnail_url}
            alt={listing.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-gray-400">No image</span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-semibold text-lg mb-2 truncate" title={listing.title}>
          {listing.title}
        </h3>
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
          {listing.description}
        </p>
        <div className="flex justify-between items-center">
          <span className="text-xl font-bold text-blue-600">{formattedPrice}</span>
          <span className="text-xs text-gray-500 capitalize">{listing.condition.replace('_', ' ')}</span>
        </div>
        <div className="mt-2 text-xs text-gray-400 capitalize">
          {listing.category.replace('_', ' ')}
        </div>
      </div>
    </div>
  );
}