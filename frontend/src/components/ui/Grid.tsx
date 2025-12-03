'use client';

import createListingQueryOptions from "@/queryOptions/createListingQueryOptions";
import { useQuery } from "@tanstack/react-query";

const getListings = async(): Promise<any> => {
  const response = await fetch ("http://127.0.0.1:8000/api/v1/listings/?limit=20&offset=0&sort=recent");
  return await response.json();
};

export function Grid() {

  const { data, error } = useQuery(createListingQueryOptions());

  if (error) {
    return <div>error</div>
  }

  return (
    <>
      <div>{JSON.stringify(data)}</div>
      <button onClick={ () => alert("button is cllicked")  }>click me</button>
    </>
  );
};