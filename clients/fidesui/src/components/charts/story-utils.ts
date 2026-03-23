export const seededRandom = (seed: number) => {
  let state = seed === 0 ? 1 : seed;
  return () => {
    state = (state * 16807 + 0) % 2147483647;
    return (state - 1) / 2147483646;
  };
};
