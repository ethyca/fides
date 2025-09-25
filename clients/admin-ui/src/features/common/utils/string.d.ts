export type StringLiteral<T> = T extends string
  ? string extends T
    ? never
    : T
  : never;
