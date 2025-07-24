import { FidesGlobal, FidesOptions } from "fides-js";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: Partial<FidesOptions>;
  }
}

export {};
