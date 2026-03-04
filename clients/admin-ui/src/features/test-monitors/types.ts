export interface RunStatus {
  step:
    | "idle"
    | "creating-connection"
    | "creating-monitor"
    | "executing"
    | "done"
    | "error";
  message?: string;
  executionId?: string;
}

export function makeKey(prefix: string) {
  return `${prefix}-${Date.now()}`;
}

/** Random integer in [min, max] inclusive */
export function randInt(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/** Random float rounded to `decimals` places in [min, max] */
export function randFloat(min: number, max: number, decimals = 2) {
  const val = Math.random() * (max - min) + min;
  return parseFloat(val.toFixed(decimals));
}
