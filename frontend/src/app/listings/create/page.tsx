"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function CreateListingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-950 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Create New Listing</h1>
          <p className="text-gray-400">List an item for sale on campus</p>
        </div>

        <div className="bg-gray-900 rounded-lg p-8">
          <p className="text-gray-300 text-center py-12">
            Listing creation form coming soon...
          </p>
          <div className="flex justify-center">
            <Button
              variant="outline"
              onClick={() => router.back()}
              className="mt-4"
            >
              Go Back
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
