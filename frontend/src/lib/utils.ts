import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Category } from "@/types/listing/filters/category";
import { Condition } from "@/types/listing/filters/condition";
import { Sort } from "@/types/listing/filters/sort";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCategoryLabel(category: Category): string {
  const labels: Record<Category, string> = {
    electronics: "Electronics",
    textbooks: "Textbooks",
    furniture: "Furniture",
    dorm: "Dorm",
    appliances: "Appliances",
    clothing: "Clothing",
    shoes: "Shoes",
    accessories: "Accessories",
    bikes: "Bikes",
    sports_equipment: "Sports Equipment",
    tools: "Tools",
    office_supplies: "Office Supplies",
    music: "Music",
    musical_instruments: "Musical Instruments",
    video_games: "Video Games",
    collectibles: "Collectibles",
    art: "Art",
    baby_kids: "Baby & Kids",
    pet_supplies: "Pet Supplies",
    tickets: "Tickets",
    services: "Services",
    other: "Other",
  };
  return labels[category];
}

export function formatConditionLabel(condition: Condition): string {
  const labels: Record<Condition, string> = {
    new: "New",
    like_new: "Like New",
    good: "Good",
    fair: "Fair",
    poor: "Poor",
  };
  return labels[condition];
}

export function formatSortLabel(sort: Sort): string {
  const labels: Record<Sort, string> = {
    recent: "Most Recent",
    price_asc: "Price: Low to High",
    price_desc: "Price: High to Low",
  };
  return labels[sort];
}

export function formatPrice(price: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(price);
}
