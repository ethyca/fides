import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import { act, renderHook } from "@testing-library/react";

// Mock the toast hook
const mockToast = jest.fn();
jest.mock("fidesui", () => ({
  useChakraToast: () => mockToast,
}));

// Mock the RTK Query lazy query hook
const mockDownloadTrigger = jest.fn();
jest.mock(
  "../../../../src/features/asset-reporting/asset-reporting.slice",
  () => ({
    useLazyDownloadAssetReportQuery: jest.fn(() => [
      mockDownloadTrigger,
      { isFetching: false },
    ]),
  }),
);

// Mock the error helper
jest.mock("../../../../src/features/common/helpers", () => ({
  getErrorMessage: jest.fn(
    (error: unknown, defaultMessage: string) => defaultMessage,
  ),
}));

// Import after mocks
// eslint-disable-next-line import/first
import useAssetReportingDownload from "../../../../src/features/asset-reporting/hooks/useAssetReportingDownload";

describe("useAssetReportingDownload", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDownloadTrigger.mockReset();
    mockToast.mockReset();
  });

  it("returns downloadReport function and loading state", () => {
    const { result } = renderHook(() => useAssetReportingDownload());

    expect(typeof result.current.downloadReport).toBe("function");
    expect(result.current.isDownloadingReport).toBe(false);
  });

  it("shows error toast on failed response", async () => {
    mockDownloadTrigger.mockResolvedValue({
      isError: true,
      error: new Error("Network error"),
    });

    const { result } = renderHook(() => useAssetReportingDownload());

    await act(async () => {
      await result.current.downloadReport({});
    });

    // Verify error toast was shown
    expect(mockToast).toHaveBeenCalledWith({
      status: "error",
      description:
        "A problem occurred while generating your asset report. Please try again.",
    });
  });

  it("passes filters to the download trigger", async () => {
    mockDownloadTrigger.mockResolvedValue({
      isError: true, // Using error to avoid blob/URL creation
      error: new Error("Test"),
    });

    const { result } = renderHook(() => useAssetReportingDownload());

    const filters = {
      asset_type: ["Cookie", "Image"],
      consent_status: ["WITH_CONSENT" as const],
      data_uses: ["analytics"],
      search: "test",
    };

    await act(async () => {
      await result.current.downloadReport(filters);
    });

    expect(mockDownloadTrigger).toHaveBeenCalledWith(filters);
  });

  it("calls downloadTrigger when downloadReport is called", async () => {
    mockDownloadTrigger.mockResolvedValue({
      isError: true,
      error: new Error("Test"),
    });

    const { result } = renderHook(() => useAssetReportingDownload());

    await act(async () => {
      await result.current.downloadReport({});
    });

    expect(mockDownloadTrigger).toHaveBeenCalledTimes(1);
    expect(mockDownloadTrigger).toHaveBeenCalledWith({});
  });
});
