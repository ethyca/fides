import type { UploadFile } from "fidesui";

import {
  uploadAllFiles,
  uploadFieldFiles,
  uploadFile,
} from "~/components/modals/privacy-request-modal/fileUploadUtils";

const API_URL = "http://localhost:8080/api/v1";

const defaultContext = {
  propertyId: "prop_123",
  policyKey: "default_access_policy",
  fieldName: "documents",
};

const mockFile = new File(["hello"], "hello.txt", { type: "text/plain" });

/** Helper to build a minimal UploadFile-like object. */
const makeUploadFile = (uid: string, originFileObj?: File): UploadFile =>
  ({
    uid,
    name: originFileObj?.name ?? uid,
    originFileObj,
  }) as UploadFile;

// ---------------------------------------------------------------------------
// uploadFile
// ---------------------------------------------------------------------------
describe("uploadFile", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("returns the attachment id on success", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "abc123" }),
    });

    const id = await uploadFile(mockFile, API_URL, defaultContext);
    expect(id).toBe("abc123");

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toBe(`${API_URL}/privacy-request/attachment`);
    expect(init.method).toBe("POST");
    expect(init.body).toBeInstanceOf(FormData);
  });

  it("throws with the detail message when the response is not ok", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 413,
      json: async () => ({ detail: "Too large" }),
    });

    await expect(uploadFile(mockFile, API_URL, defaultContext)).rejects.toThrow(
      "Too large",
    );
  });

  it("throws with a generic message when the error body is unparseable", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("not json");
      },
    });

    await expect(uploadFile(mockFile, API_URL, defaultContext)).rejects.toThrow(
      "File upload failed (500)",
    );
  });

  it("does not append property_id to FormData when propertyId is empty", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "id1" }),
    });

    await uploadFile(mockFile, API_URL, {
      ...defaultContext,
      propertyId: "",
    });

    const { body } = (global.fetch as jest.Mock).mock.calls[0][1];
    expect(body.get("property_id")).toBeNull();
    expect(body.get("policy_key")).toBe("default_access_policy");
  });
});

// ---------------------------------------------------------------------------
// uploadFieldFiles
// ---------------------------------------------------------------------------
describe("uploadFieldFiles", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("filters out entries that lack originFileObj", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ id: "id1" }),
    });

    const fileList: UploadFile[] = [
      makeUploadFile("no-file"),
      makeUploadFile("has-file", mockFile),
    ];

    const ids = await uploadFieldFiles(fileList, API_URL, defaultContext);
    expect(ids).toEqual(["id1"]);
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("returns IDs in order for files that have originFileObj", async () => {
    const file1 = new File(["a"], "a.txt");
    const file2 = new File(["b"], "b.txt");

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "id-a" }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "id-b" }) });

    const fileList: UploadFile[] = [
      makeUploadFile("1", file1),
      makeUploadFile("2", file2),
    ];

    const ids = await uploadFieldFiles(fileList, API_URL, defaultContext);
    expect(ids).toEqual(["id-a", "id-b"]);
  });

  it("propagates error if one upload fails mid-sequence", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: "id-ok" }) })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "server error" }),
      });

    const fileList: UploadFile[] = [
      makeUploadFile("1", new File(["a"], "a.txt")),
      makeUploadFile("2", new File(["b"], "b.txt")),
    ];

    await expect(
      uploadFieldFiles(fileList, API_URL, defaultContext),
    ).rejects.toThrow("server error");
  });
});

// ---------------------------------------------------------------------------
// uploadAllFiles
// ---------------------------------------------------------------------------
describe("uploadAllFiles", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const baseContext = { propertyId: "prop_1", policyKey: "policy_1" };

  it("skips fields with empty file lists", async () => {
    const values = { docs: [] as UploadFile[] };
    const fields = { docs: { field_type: "file" } };

    const result = await uploadAllFiles(values, fields, API_URL, baseContext);
    expect(result).toEqual({});
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("skips non-file-type fields", async () => {
    const values = { reason: "some text" };
    const fields = { reason: { field_type: "text" } };

    const result = await uploadAllFiles(values, fields, API_URL, baseContext);
    expect(result).toEqual({});
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("returns correct fieldKey to id[] map for populated file fields", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "att-1" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "att-2" }),
      });

    const values = {
      docs: [
        makeUploadFile("f1", new File(["a"], "a.pdf")),
        makeUploadFile("f2", new File(["b"], "b.pdf")),
      ] as UploadFile[],
      reason: "some text",
    };

    const fields = {
      docs: { field_type: "file" },
      reason: { field_type: "text" },
    };

    const result = await uploadAllFiles(values, fields, API_URL, baseContext);
    expect(result).toEqual({ docs: ["att-1", "att-2"] });
  });

  it("omits fields from result when no IDs are produced", async () => {
    // All entries lack originFileObj, so no uploads happen and no IDs are produced.
    const values = {
      docs: [makeUploadFile("no-origin")] as UploadFile[],
    };
    const fields = { docs: { field_type: "file" } };

    const result = await uploadAllFiles(values, fields, API_URL, baseContext);
    expect(result).toEqual({});
  });
});
