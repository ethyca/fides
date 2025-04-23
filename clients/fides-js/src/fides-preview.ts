// This script provides a way to dynamically switch between different Fides builds
// for preview purposes. It's used by the Admin UI to test different configurations.

// Import FidesGlobal type from the main Fides script
import type { FidesGlobal } from "./fides";

declare global {
  interface Window {
    Fides: FidesGlobal;
    FidesPreview: {
      (mode?: "standard" | "tcf"): void;
      cleanup: () => void;
    };
  }
}

// These will be replaced with actual script contents during build
declare const FIDES_STANDARD_SCRIPT: string;
declare const FIDES_TCF_SCRIPT: string;

// Store the script contents but don't execute them
const scripts = {
  standard: FIDES_STANDARD_SCRIPT,
  tcf: FIDES_TCF_SCRIPT,
};

// Track current state
let currentMode: string | null = null;
let currentScript: HTMLScriptElement | null = null;

// Cleanup function to remove previous execution
function cleanup(): void {
  if (currentScript) {
    // Remove the script from DOM to ensure complete cleanup
    currentScript.remove();
    currentScript = null;
    // @ts-ignore - We know this is safe as we're cleaning up the global
    window.Fides = null;
  }
  currentMode = null;
}

// Global control method
function FidesPreview(mode: "standard" | "tcf" = "standard"): void {
  if (currentMode === mode) {
    return; // Already in this mode
  }

  // Clean up previous execution
  cleanup();

  // Create and execute new script
  currentScript = document.createElement("script");
  currentScript.textContent = scripts[mode];
  currentMode = mode;

  // Execute the new script
  document.head.appendChild(currentScript);
}

// Attach cleanup function
FidesPreview.cleanup = cleanup;

// Expose to window
window.FidesPreview = FidesPreview;

// Export for module usage
export { FidesPreview };
