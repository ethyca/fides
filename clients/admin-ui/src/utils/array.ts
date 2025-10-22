/**
 *  Array based utilities
 */
import { A, NonEmptyArray } from "./array.d";

export const isEmpty = <T>(a: A<T>): a is never[] => a.length < 1;

export const isNotEmpty = <T>(a: A<T>): a is NonEmptyArray<T> => a.length >= 1;

export const unique = <T>(a: A<T>): Readonly<A<T>> => [...new Set(a)];

export const intersection = <T>(l: A<T>, r: A<T>): A<T> =>
  unique([...l, ...r]).flatMap((m) =>
    l.includes(m) && r.includes(m) ? [m] : [],
  );

export const fold = <T>(a: A<T>, f: (l: T, r: T) => T): T | undefined => {
  const [first, ...rest] = a;

  return rest.reduce<T>(f, first);
};
