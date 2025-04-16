export {};

declare global {
  interface Window {
    Cypress?: boolean;
    FidesPreview: {
      (mode: string): void;
      cleanup: () => void;
    };
  }
}
