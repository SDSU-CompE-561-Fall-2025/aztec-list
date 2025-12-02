import Card from "./card";
import { ListingSummary } from "@/lib/types";

interface GridProps {
  listings: ListingSummary[];
}

export default function Grid({ listings }: GridProps) {
  return (
    <div className="grid justify-center gap-4 grid-cols-[repeat(auto-fit,minmax(250px,1fr))]">
      {listings.map((listing) => (
        <Card key={listing.id} listing={listing} />
      ))}
    </div>
  );
}