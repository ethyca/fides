import { CmpApi } from "@iabgpp/cmpapi";

import {
  consentIdsFromAcString,
  decodeFidesString,
  formatFidesStringWithGpp,
} from "../../src/lib/fides-string";

describe("fidesString", () => {
  beforeAll(() => {
    window.Fides = {
      options: { tcfEnabled: false },
      fides_string: undefined,
    } as any;
    window.fidesDebugger = () => {};
    // eslint-disable-next-line no-underscore-dangle
    window.__gpp = () => {};
  });

  beforeEach(() => {
    window.Fides.options.tcfEnabled = false;
    window.Fides.fides_string = undefined;
  });

  describe("decodeFidesString", () => {
    it.each([
      // Empty string
      {
        fidesString: "",
        expected: { tc: "", ac: "", gpp: "", nc: "" },
      },
      // TC string only
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "",
          gpp: "",
          nc: "",
        },
      },
      // Without vendors disclosed
      {
        fidesString: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA",
          ac: "",
          gpp: "",
          nc: "",
        },
      },
      // Invalid case of only AC string- need core TC string
      {
        fidesString: ",2~2.3.4~dv.1.5",
        expected: { tc: "", ac: "", gpp: "", nc: "" },
      },
      // Both TC and AC string
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,2~2.3.4~dv.1.5",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "2~2.3.4~dv.1.5",
          gpp: "",
          nc: "",
        },
      },
      // GPP string only
      {
        fidesString: ",,DBABLA~BVAUAAAAAWA.QA",
        expected: { tc: "", ac: "", gpp: "DBABLA~BVAUAAAAAWA.QA", nc: "" },
      },
      // TC + GPP string
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,,DBABLA~BVAUAAAAAWA.QA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "",
          gpp: "DBABLA~BVAUAAAAAWA.QA",
          nc: "",
        },
      },
      // Complete string (TC + AC + GPP)
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,2~2.3.4~dv.1.5,DBABLA~BVAUAAAAAWA.QA",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "2~2.3.4~dv.1.5",
          gpp: "DBABLA~BVAUAAAAAWA.QA",
          nc: "",
        },
      },
      // No trailing comma when no GPP
      {
        fidesString:
          "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA,2~2.3.4~dv.1.5",
        expected: {
          tc: "CPzvOIAPzvOIAGXABBENAUEAAACAAAAAAAAAAAAAAAAA.IAAA",
          ac: "2~2.3.4~dv.1.5",
          gpp: "",
          nc: "",
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

  describe("consentIdsFromAcString", () => {
    it.each([
      // Empty string
      {
        acString: "",
        expected: [],
      },
      // String without ids
      {
        acString: "2~~dv.",
        expected: [],
      },
      // Invalid string
      {
        acString: "invalid",
        expected: [],
      },
      // Proper v1 string
      {
        acString: "2~1.2.3~dv.4.5",
        expected: ["gacp.1", "gacp.2", "gacp.3"],
      },
      // Proper v2 string
      {
        acString: "2~1.2.3~dv.4.5",
        expected: ["gacp.1", "gacp.2", "gacp.3"],
      },
    ])(
      "can decode a fides string of varying formats",
      ({ acString, expected }) => {
        const result = consentIdsFromAcString(acString);
        expect(result).toEqual(expected);
      },
    );
  });

  describe("formatFidesStringWithGpp", () => {
    describe("in a non-TCF experience", () => {
      beforeEach(() => {
        window.Fides.options.tcfEnabled = false;
      });

      it("formats GPP string with empty TC and AC parts", () => {
        const cmpApi = new CmpApi(1, 1);
        // Mock the GPP string
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(",,DBABLA~BVAUAAAAAWA.QA");
      });
    });

    describe("in a TCF experience", () => {
      beforeEach(() => {
        window.Fides.options.tcfEnabled = true;
      });

      it("appends GPP string to existing TC and AC strings", () => {
        const cmpApi = new CmpApi(1, 1);
        window.Fides.fides_string = "CPzvOIA.IAAA,2~2.3.4~dv.1.5";
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(
          "CPzvOIA.IAAA,2~2.3.4~dv.1.5,DBABLA~BVAUAAAAAWA.QA",
        );
      });

      it("appends GPP string to TC string when AC string is empty", () => {
        const cmpApi = new CmpApi(1, 1);
        window.Fides.fides_string = "CPzvOIA.IAAA";
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe("CPzvOIA.IAAA,,DBABLA~BVAUAAAAAWA.QA");
      });

      it("appends GPP string when no existing fides_string", () => {
        const cmpApi = new CmpApi(1, 1);
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(",,DBABLA~BVAUAAAAAWA.QA");
      });

      it("injects GPP string to existing TC, AC, and NC strings", () => {
        const cmpApi = new CmpApi(1, 1);
        window.Fides.fides_string =
          "CPzvOIA.IAAA,2~2.3.4~dv.1.5,,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9";
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(
          "CPzvOIA.IAAA,2~2.3.4~dv.1.5,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9",
        );
      });

      it("injects GPP string to TC string when AC string is empty and NC string exists", () => {
        const cmpApi = new CmpApi(1, 1);
        window.Fides.fides_string =
          "CPzvOIA.IAAA,,,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9";
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(
          "CPzvOIA.IAAA,,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9",
        );
      });

      it("injects GPP string when only NC string exists", () => {
        const cmpApi = new CmpApi(1, 1);
        window.Fides.fides_string =
          ",,,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9";
        jest
          .spyOn(cmpApi, "getGppString")
          .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

        const result = formatFidesStringWithGpp(cmpApi);
        expect(result).toBe(
          ",,DBABLA~BVAUAAAAAWA.QA,eyJkYXRhX3NhbGVzX2FuZF9zaGFyaW5nIjoxLCJhbmFseXRpY3MiOjB9",
        );
      });
    });
  });
});
