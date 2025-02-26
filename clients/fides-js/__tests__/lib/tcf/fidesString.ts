import {
  decodeFidesString,
  idsFromAcString,
} from "../../../src/lib/tcf/fidesString";

describe("fidesString", () => {
  beforeAll(() => {
    window.fidesDebugger = () => {};
  });
  describe("decodeFidesString", () => {
    it.each([
      // Empty string
      {
        fidesString: "",
        expected: { tc: "", ac: "" },
      },
      // TC string only
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "",
        },
      },
      // Without vendors disclosed
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
          ac: "",
        },
      },
      // Invalid case of only AC string- need core TC string
      {
        fidesString: ",1~2.3.4",
        expected: { tc: "", ac: "" },
      },
      // Both TC and AC string
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
        },
      },
      // With extra unexpected stuff
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4,extrastuff",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
        },
      },
    ])(
      "can decode a fides string of varying formats",
      ({ fidesString, expected }) => {
        const result = decodeFidesString(fidesString);
        expect(result).toEqual(expected);
      },
    );
  });

  describe("idsFromAcString", () => {
    it.each([
      // Empty string
      {
        acString: "",
        expected: [],
      },
      // String without ids
      {
        acString: "1~",
        expected: [],
      },
      // Invalid string
      {
        acString: "invalid",
        expected: [],
      },
      // Proper string
      {
        acString: "1~1.2.3",
        expected: ["gacp.1", "gacp.2", "gacp.3"],
      },
    ])(
      "can decode a fides string of varying formats",
      ({ acString, expected }) => {
        const result = idsFromAcString(acString);
        expect(result).toEqual(expected);
      },
    );
  });
});
