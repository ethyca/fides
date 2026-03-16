import type { ReactNode } from "react";
import { useSyncExternalStore } from "react";

export interface DashboardDrawerState {
  title: string;
  width?: number;
  content: ReactNode;
}

let drawerState: DashboardDrawerState | null = null;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export function openDashboardDrawer(state: DashboardDrawerState) {
  drawerState = state;
  emit();
}

export function closeDashboardDrawer() {
  drawerState = null;
  emit();
}

export function useDashboardDrawer(): DashboardDrawerState | null {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => {
        listeners.delete(cb);
      };
    },
    () => drawerState,
    () => drawerState,
  );
}
