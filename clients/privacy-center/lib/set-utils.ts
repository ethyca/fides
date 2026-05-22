export const setsEqual = (a: Set<string>, b: Set<string>): boolean => {
  if (a.size !== b.size) {
    return false;
  }
  const arr = Array.from(a);
  return arr.every((item) => b.has(item));
};
