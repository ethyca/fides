export const setsEqual = (a: Set<string>, b: Set<string>): boolean => {
  if (a.size !== b.size) {
    return false;
  }
  let equal = true;
  a.forEach((item) => {
    if (!b.has(item)) {
      equal = false;
    }
  });
  return equal;
};
