export const CONDITIONS = ["new", "like_new", "good", "fair", "poor"] as const;

export type Condition = (typeof CONDITIONS)[number];
