import type { AppStore } from "~/app/store";

declare global {
  interface Window {
    store?: AppStore;
    Cypress?: boolean;
  }
}

export {};
