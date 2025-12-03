'use client';

import { useQuery } from "@tanstack/react-query";

const getListings = async(): Promise<any> => {
  const response = await fetch ("http://127.0.0.1:8000/api/v1/listings/?limit=20&offset=0&sort=recent");
  return await response.json();
};

export function Grid() {

  const { data, refetch } = useQuery({
    queryKey: ["listings"],
    queryFn: getListings,
  });

  return (
    <div>{JSON.stringify(data)}</div>
  );
};