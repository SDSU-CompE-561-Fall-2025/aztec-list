'use client';

import createListingQueryOptions from "@/queryOptions/createListingQueryOptions";
import { useQuery } from "@tanstack/react-query";
import { Input } from "../ui/input";
import { Search } from "./search";

export function Grid() {

  const { data } = useQuery(createListingQueryOptions());

  return (
    <>
      <Search></Search>
    </>
  );
};