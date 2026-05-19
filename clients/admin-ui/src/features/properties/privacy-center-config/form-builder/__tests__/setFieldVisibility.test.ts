import { addField, emptySpec, setFieldVisibility } from "../specMutations";

describe("setFieldVisibility", () => {
  it("attaches a visible condition to the target element", () => {
    const start = addField(emptySpec(), "Text").spec;
    const id = start.elements.form.children[0];
    const cond = [{ $state: "/form/country", eq: "US" }];
    const next = setFieldVisibility(start, id, cond);
    expect((next.elements[id] as { visible?: unknown }).visible).toEqual(cond);
  });

  it("removes the visible key when passed undefined", () => {
    const start = addField(emptySpec(), "Text").spec;
    const id = start.elements.form.children[0];
    const withCond = setFieldVisibility(start, id, [
      { $state: "/form/country", eq: "US" },
    ]);
    const cleared = setFieldVisibility(withCond, id, undefined);
    expect("visible" in cleared.elements[id]).toBe(false);
  });

  it("returns the spec unchanged for an unknown element id", () => {
    const start = addField(emptySpec(), "Text").spec;
    expect(
      setFieldVisibility(start, "nope", [{ $state: "/x", eq: 1 }]),
    ).toEqual(start);
  });
});
