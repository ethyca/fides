import { inspectForBrowserIdentities } from "~/common/browser-identities";

const mockCookie = (value: str) => {
  Object.defineProperty(window.document, "cookie", {
    writable: true,
    value,
  });
};

const clientId = "968159977.1674053816";
const gaCookie = `_ga=GA1.1.${clientId}`;

describe("browser identities", () => {
  it("can inspect for a google analytics cookie when it is the only cookie", () => {
    mockCookie(`${gaCookie};`);
    const identity = inspectForBrowserIdentities();
    expect(identity).toEqual(clientId);
  });

  it("can inspect for a google analytics cookie when it is one of many cookies", () => {
    mockCookie(`cookie1=value1; ${gaCookie}; cookie2=value2;`);
    const identity = inspectForBrowserIdentities();
    expect(identity).toEqual(clientId);
  });

  it("returns undefined if no ga cookie exists", () => {
    // wrong key
    mockCookie(`_gaFake=GA1.1.${clientId}`);
    expect(inspectForBrowserIdentities()).toBe(undefined);

    // malformed cookie
    mockCookie(`_ga=GA1.1.`);
    expect(inspectForBrowserIdentities()).toBe(undefined);
  });
});
