import { chunkItems, PAGE_SIZE } from "../../src/lib/paging";

describe("chunkItems", () => {
  it.each([
    { label: "few items", items: [1, 2, 3], expected: [[1, 2, 3]] },
    { label: "no items", items: [], expected: [] },
    {
      label: "many items multiple of page size",
      items: Array(PAGE_SIZE * 2).fill(0),
      expected: [Array(PAGE_SIZE).fill(0), Array(PAGE_SIZE).fill(0)],
    },
    {
      label: "many items with a remainder",
      items: Array(PAGE_SIZE * 2 + 3).fill(0),
      expected: [Array(PAGE_SIZE).fill(0), Array(PAGE_SIZE).fill(0), [0, 0, 0]],
    },
  ])("pages correctly when there are $label", ({ items, expected }) => {
    expect(chunkItems(items)).toEqual(expected);
  });
});
