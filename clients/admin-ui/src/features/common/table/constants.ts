export const DEFAULT_PAGE_SIZES = [25, 50, 100] as const;
export const DEFAULT_PAGE_SIZE: (typeof DEFAULT_PAGE_SIZES)[number] = 25;
export const DEFAULT_PAGE_INDEX = 1; // ant design pagination is 1-indexed, so use 1 not 0
