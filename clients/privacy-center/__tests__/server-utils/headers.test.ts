import {
  applyRequestContext,
  getApplicableHeaderRules,
  HeaderRule,
  MiddlewareResponseInit,
} from "~/app/server-utils/headers";

describe("header utilities", () => {
  describe(getApplicableHeaderRules, () => {
    it("returns the first matching header definition for a path", () => {
      const expectedHeaders: [string, string] = ["header-1", "value-1"];
      const headers: HeaderRule[] = [
        { matcher: /\/a/, headers: [expectedHeaders] },
        { matcher: /\/a/, headers: [["header-1", "value-2"]] },
      ];

      expect(
        getApplicableHeaderRules("/a", headers).headerDefinitions,
      ).toStrictEqual([expectedHeaders]);
    });

    it("returns disparate headers", () => {
      const header1 = "header-1";
      const header2 = "header-2";
      const headers1: [string, string] = [header1, "value-1"];
      const headers2: [string, string] = [header2, "value-2"];
      const headers: HeaderRule[] = [
        { matcher: /\/a-path/, headers: [headers1] },
        { matcher: /\/a-path/, headers: [headers2] },
      ];

      expect(
        getApplicableHeaderRules("/a-path", headers).headerDefinitions,
      ).toStrictEqual([headers1, headers2]);
    });

    it("returns context appliers that match", () => {
      const applier = () => {};
      const header: HeaderRule = {
        matcher: /\/a-path/,
        headers: [
          { name: "header-1", value: () => "value-1", context: applier },
        ],
      };
      const rules = getApplicableHeaderRules("/a-path", [header]);
      expect(rules.contextAppliers).toHaveLength(1);
      expect(rules.contextAppliers[0]).toBe(applier);
    });
  });

  describe(applyRequestContext, () => {
    test("that the request context can be changed by the applier", () => {
      const headers = new Headers();
      const context: MiddlewareResponseInit = {
        request: {
          headers,
        },
      };

      applyRequestContext(
        [
          (controller) => {
            controller.setContext("header-1", "value-1");
          },
        ],
        context,
      );

      expect(headers.get("header-1")).toBe("value-1");
    });

    test("that a previous context variable can be retrieved", () => {
      const headers = new Headers();
      const context: MiddlewareResponseInit = {
        request: {
          headers,
        },
      };

      headers.set("header-1", "value-1");

      applyRequestContext(
        [
          (controller) => {
            expect(controller.hasContext("header-1")).toBeTruthy();
            expect(controller.hasContext("header-2")).toBeFalsy();
            expect(controller.getContext("header-1")).toBe("value-1");
          },
        ],
        context,
      );
    });
  });
});
