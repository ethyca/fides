/**
 * Index into an object with possibility of nesting
 *
 * Ex:
 * obj = {
 *   a : {
 *     b: 'hi'
 *   }
 * }
 * resolvePath(obj, 'a') --> { b: 'hi' }
 * resolvePath(obj, 'a.b') --> 'hi'
 *
 * @param object The object to index into
 * @param path String path to use as a key
 * @returns
 */
export const resolvePath = (object: unknown, path: string): unknown =>
  path
    .split(".")
    .reduce(
      (o: unknown, p) =>
        typeof o === "object" && o !== null
          ? (o as Record<string, unknown>)[p]
          : undefined,
      object,
    );
