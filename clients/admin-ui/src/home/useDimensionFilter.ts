import { useSyncExternalStore } from "react";

let activeDimension: string | null = null;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot() {
  return activeDimension;
}

export function setDimensionFilter(dimension: string) {
  activeDimension = activeDimension === dimension ? null : dimension;
  emit();
}

export function clearDimensionFilter() {
  activeDimension = null;
  emit();
}

export function useDimensionFilter(): string | null {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
