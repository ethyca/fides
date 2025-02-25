import { CmpApi } from "@iabgpp/cmpapi";

import { GppFunction } from "~/lib/gpp/types";

import { formatFidesStringWithGpp } from "../../../src/lib/fidesString";

declare global {
  interface Window {
    __gpp?: GppFunction;
  }
}

describe("formatFidesStringWithGpp", () => {
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

  it("uses default GPP string when no CmpApi is provided", () => {
    const result = formatFidesStringWithGpp();
    expect(result).toBe(",,DBAA");
  });

  // it("uses default GPP string when CmpApi returns no string", () => {
  //   const cmpApi = new CmpApi(1, 1);
  //   jest.spyOn(cmpApi, "getGppString").mockReturnValue("");
  //   const result = formatFidesStringWithGpp(cmpApi);
  //   expect(result).toBe(",,DBAA");
  // });

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

    it("appends default GPP string to existing TC and AC strings when no CmpApi provided", () => {
      window.Fides.fides_string = "CPzvOIA.IAAA,1~2.3.4";
      const result = formatFidesStringWithGpp();
      expect(result).toBe("CPzvOIA.IAAA,1~2.3.4,DBAA");
    });

    it("appends GPP string to existing TC and AC strings", () => {
      const cmpApi = new CmpApi(1, 1);
      window.Fides.fides_string = "CPzvOIA.IAAA,1~2.3.4";
      jest
        .spyOn(cmpApi, "getGppString")
        .mockReturnValue("DBABLA~BVAUAAAAAWA.QA");

      const result = formatFidesStringWithGpp(cmpApi);
      expect(result).toBe("CPzvOIA.IAAA,1~2.3.4,DBABLA~BVAUAAAAAWA.QA");
    });

    it("appends GPP string to TC string when AC string is empty", () => {
      const cmpApi = new CmpApi(1, 1);
      window.Fides.fides_string = "CPzvOIA.IAAA,";
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
  });
});
