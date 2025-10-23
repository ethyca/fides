export type A<T> = Readonly<Array<T>> | Array<T>;

export type NonEmptyArray<T> = [T, ...T[]];
