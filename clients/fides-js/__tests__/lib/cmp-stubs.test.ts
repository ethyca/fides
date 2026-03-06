/* eslint-disable no-underscore-dangle */
import { updateTcfStubGdprApplies } from "~/lib/cmp-stubs";

describe("updateTcfStubGdprApplies", () => {
  afterEach(() => {
    delete (window as any).__tcfapi;
  });

  it("does nothing when window.__tcfapi is not defined", () => {
    expect(() => updateTcfStubGdprApplies()).not.toThrow();
  });

  it("does nothing when window.__tcfapi is not a function", () => {
    (window as any).__tcfapi = "not a function";
    expect(() => updateTcfStubGdprApplies()).not.toThrow();
  });

  it("calls setGdprApplies with false when window.__tcfapi exists", () => {
    const mockTcfApi = jest.fn();
    (window as any).__tcfapi = mockTcfApi;

    updateTcfStubGdprApplies();

    expect(mockTcfApi).toHaveBeenCalledTimes(1);
    expect(mockTcfApi).toHaveBeenCalledWith(
      "setGdprApplies",
      2,
      expect.any(Function),
      false,
    );
  });
});
