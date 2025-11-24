import { NextResponse } from "next/server";

import {
  applyRequestContext,
  applyResponseHeaders,
  getApplicableHeaderRules,
  HeaderRule,
  MiddlewareResponseInit,
} from "~/app/server-utils/headers";

const contextFactory = jest.fn<MiddlewareResponseInit, []>(() => ({
  request: { headers: new Headers() },
}));

describe("header utilities", () => {
  afterEach(() => {
    contextFactory.mockClear();
  });

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
      const context = contextFactory();

      applyRequestContext(
        [
          (controller) => {
            controller.setContext("header-1", "value-1");
          },
        ],
        context,
      );

      expect(context.request.headers.get("header-1")).toBe("value-1");
    });

    test("that a previous context variable can be retrieved", () => {
      const context = contextFactory();

      context.request.headers.set("header-1", "value-1");

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

  describe(applyResponseHeaders, () => {
    test("that simple response headers are applied", () => {
      const context = contextFactory();
      const response = NextResponse.next(context);

      applyResponseHeaders(context, [["header-1", "value-1"]], response);

      expect(response.headers.get("header-1")).toBe("value-1");
    });

    test("that dynamic response headers are applied", () => {
      const context = contextFactory();
      const response = NextResponse.next(context);

      applyResponseHeaders(
        context,
        [{ name: "header-1", value: () => "value-1" }],
        response,
      );

      expect(response.headers.get("header-1")).toBe("value-1");
    });
  });
});
