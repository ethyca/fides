export function generateDefaultKey(prefix: string) {
  return `${prefix}-${Date.now()}`;
}

/** Random integer in [min, max] inclusive */
export function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
