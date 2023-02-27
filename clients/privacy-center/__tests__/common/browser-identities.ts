import { inspectForBrowserIdentities } from "~/common/browser-identities";

const mockCookie = (value: string) => {
  Object.defineProperty(window.document, "cookie", {
    writable: true,
    value,
  });
};

// google
const clientId = "999999999.8888888888";
const gaCookie = `_ga=GA1.1.${clientId}`;

// sovrn
const sovrnCookie = "ljt_readerID=test";

describe("browser identities", () => {
  it("can inspect for a google analytics cookie when it is the only cookie", () => {
    mockCookie(`${gaCookie};`);
    const identity = inspectForBrowserIdentities();
    expect(identity?.ga_client_id).toEqual(clientId);
  });

  it("can inspect for a google analytics cookie when it is one of many cookies", () => {
    mockCookie(`cookie1=value1; ${gaCookie}; cookie2=value2;`);
    const identity = inspectForBrowserIdentities();
    expect(identity?.ga_client_id).toEqual(clientId);
  });

  it("returns undefined if no ga cookie exists", () => {
    // wrong key
    mockCookie(`_gaFake=GA1.1.${clientId}`);
    expect(inspectForBrowserIdentities()).toBe(undefined);

    // malformed cookie
    mockCookie(`_ga=GA1.1.`);
    expect(inspectForBrowserIdentities()?.ga_client_id).toBe(undefined);
  });

  it("can inspect for a sovrn cookie", () => {
    mockCookie(`${sovrnCookie};`);
    const identity = inspectForBrowserIdentities();
    expect(identity?.ljt_readerID).toEqual("test");
  });

  it("can inspect for both ga and sovrn", () => {
    mockCookie(`${sovrnCookie}; ${gaCookie}`);
    const identity = inspectForBrowserIdentities();
    expect(identity).toEqual({ ga_client_id: clientId, ljt_readerID: "test" });
  });
});
