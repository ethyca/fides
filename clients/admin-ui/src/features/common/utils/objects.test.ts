import { describe, expect, it } from "@jest/globals";

import { mappedZip, zip } from "~/features/common/utils/objects";

describe(zip.name, () => {
  it("returns matched pairs", () => {
    const result = zip(
      {
        a: true,
        b: 0,
        c: "",
        d: {},
        e: null,
        f: "left first",
        g: "left second",
      },
      {
        a: false,
        b: 10,
        c: "test",
        d: { attr: "string" },
        e: undefined,
        g: "right first",
        f: "right second",
      },
    );
    expect(result).toStrictEqual({
      a: [true, false],
      b: [0, 10],
      c: ["", "test"],
      d: [{}, { attr: "string" }],
      e: [null, undefined],
      f: ["left first", "right second"],
      g: ["left second", "right first"],
    });
  });

  it("returns unmatched pairs", () => {
    const result = zip(
      {
        a: true,
        c: "",
        e: null,
        g: "left second",
      },
      {
        b: 10,
        d: { attr: "string" },
        f: "right first",
      },
    );

    expect(result).toEqual({
      a: [true, undefined],
      b: [undefined, 10],
      c: [""],
      d: [undefined, { attr: "string" }],
      e: [null],
      f: [undefined, "right first"],
      g: ["left second", undefined],
    });
  });
});

describe(mappedZip.name, () => {
  it("returns zipped values as the result of a mapping function", () => {
    const result = mappedZip(
      {
        a: "a",
        b: "b",
        c: "c",
        d: "d",
        e: "e",
      },
      {
        e: 5,
        a: 1,
        c: 3,
        b: 2,
        d: 4,
      },
      (l, r) => `${l}: ${r}`,
    );

    expect(result).toEqual({
      a: "a: 1",
      b: "b: 2",
      c: "c: 3",
      d: "d: 4",
      e: "e: 5",
    });
  });
});
