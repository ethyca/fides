/**
 * Error Report Utilities
 *
 * Provides functionality to create and download error reports for support.
 * These reports bundle error details with browser context to help FDEs
 * diagnose issues remotely.
 */

/**
 * Creates a downloadable error report bundle.
 *
 * @param errorData - The error information to include
 * @returns JSON string of the bundle
 */
export function createErrorReportBundle(errorData: {
  status?: number | string;
  message: string;
  endpoint: string;
  rawData: string;
  timestamp: number;
}): string {
  const bundle = {
    reportGeneratedAt: new Date().toISOString(),
    error: {
      occurredAt: new Date(errorData.timestamp).toISOString(),
      status: errorData.status,
      message: errorData.message,
      endpoint: errorData.endpoint,
      details: errorData.rawData,
    },
    browser: {
      userAgent: navigator.userAgent,
      language: navigator.language,
      url: window.location.href,
      screenSize: `${window.screen.width}x${window.screen.height}`,
      viewportSize: `${window.innerWidth}x${window.innerHeight}`,
    },
  };

  return JSON.stringify(bundle, null, 2);
}

/**
 * Downloads an error report as a JSON file.
 *
 * @param errorData - The error information
 */
export function downloadErrorReport(errorData: {
  status?: number | string;
  message: string;
  endpoint: string;
  rawData: string;
  timestamp: number;
}): void {
  const bundle = createErrorReportBundle(errorData);
  const blob = new Blob([bundle], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `fides-error-report-${timestamp}.json`;

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}
