'use client';

import { useQuery } from "@tanstack/react-query";

const getListings = async(): Promise<any> => {
  const response = await fetch ("http://localhost:8000/api/vi/listings");
  return await response.json();
};

const { data } = useQuery({
  queryKey: ["listings"],
  queryFn: getListings,
});

export function Grid() {
    return (
        <div>{JSON.stringify(data)}</div>
    );
};