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
        expected: { tc: "", ac: "", gpp: "" },
      },
      // TC string only
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "",
          gpp: "",
        },
      },
      // Without vendors disclosed
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
          ac: "",
          gpp: "",
        },
      },
      // Invalid case of only AC string- need core TC string
      {
        fidesString: ",1~2.3.4",
        expected: { tc: "", ac: "", gpp: "" },
      },
      // Both TC and AC string
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
          gpp: "",
        },
      },
      // GPP string only
      {
        fidesString: ",,DBABLA~BVAUAAAAAWA.QA",
        expected: { tc: "", ac: "", gpp: "DBABLA~BVAUAAAAAWA.QA" },
      },
      // TC + GPP string
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,,DBABLA~BVAUAAAAAWA.QA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "",
          gpp: "DBABLA~BVAUAAAAAWA.QA",
        },
      },
      // Complete string (TC + AC + GPP)
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4,DBABLA~BVAUAAAAAWA.QA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
          gpp: "DBABLA~BVAUAAAAAWA.QA",
        },
      },
      // No trailing comma when no GPP
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
          gpp: "",
        },
      },
      // With extra unexpected stuff
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,1~2.3.4,DBABLA~BVAUAAAAAWA.QA,extrastuff",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "1~2.3.4",
          gpp: "DBABLA~BVAUAAAAAWA.QA",
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
