import { downloadBlob } from "./useDownloadPrivacyRequestDiagnostics";

describe("downloadBlob", () => {
  const mockCreateObjectURL = jest.fn().mockReturnValue("blob:mock-url");
  const mockRevokeObjectURL = jest.fn();

  beforeEach(() => {
    URL.createObjectURL = mockCreateObjectURL;
    URL.revokeObjectURL = mockRevokeObjectURL;
  });

  afterEach(() => {
    jest.restoreAllMocks();
    mockCreateObjectURL.mockClear();
    mockRevokeObjectURL.mockClear();
  });

  it("creates an object URL from the blob and triggers download", () => {
    const clickSpy = jest.fn();
    const removeSpy = jest.fn();
    jest.spyOn(document, "createElement").mockReturnValue({
      href: "",
      download: "",
      click: clickSpy,
      remove: removeSpy,
    } as unknown as HTMLAnchorElement);

    const blob = new Blob(["test"], { type: "application/zip" });
    downloadBlob(blob, "diagnostics-abc.zip");

    expect(mockCreateObjectURL).toHaveBeenCalledWith(blob);
    expect(clickSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalled();
    expect(mockRevokeObjectURL).toHaveBeenCalledWith("blob:mock-url");
  });

  it("sets the correct filename on the download link", () => {
    let capturedDownload = "";
    jest.spyOn(document, "createElement").mockReturnValue({
      href: "",
      set download(val: string) {
        capturedDownload = val;
      },
      get download() {
        return capturedDownload;
      },
      click: jest.fn(),
      remove: jest.fn(),
    } as unknown as HTMLAnchorElement);

    const blob = new Blob(["test"]);
    downloadBlob(blob, "diagnostics-abc.zip");

    expect(capturedDownload).toBe("diagnostics-abc.zip");
  });
});
