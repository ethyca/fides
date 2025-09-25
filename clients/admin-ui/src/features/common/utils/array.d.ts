export type NonEmptyArray<T> = [T, ...T[]];

export type ReadOnlyNonEmptyArray<T> = readonly [T, ...T[]];

export type ValueOf<A extends readonly T[]> = A[number];
