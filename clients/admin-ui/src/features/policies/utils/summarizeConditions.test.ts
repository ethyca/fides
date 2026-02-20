import {
  ConditionGroup,
  ConditionLeaf,
  GroupOperator,
  Operator,
} from "~/types/api";

import { summarizeConditions } from "./summarizeConditions";

const leaf = (field: string = "user.name"): ConditionLeaf => ({
  field_address: field,
  operator: Operator.EQ,
  value: "test",
});

const group = (
  children: Array<ConditionLeaf | ConditionGroup>,
  op: GroupOperator = GroupOperator.AND,
): ConditionGroup => ({
  logical_operator: op,
  conditions: children,
});

describe("summarizeConditions", () => {
  it("returns null for null input", () => {
    expect(summarizeConditions(null)).toBeNull();
  });

  it("returns null for undefined input", () => {
    expect(summarizeConditions(undefined)).toBeNull();
  });

  it("returns singular for a single leaf", () => {
    expect(summarizeConditions(leaf())).toBe("1 condition");
  });

  it("returns singular for a group with one leaf", () => {
    expect(summarizeConditions(group([leaf()]))).toBe("1 condition");
  });

  it("returns plural for a group with multiple leaves", () => {
    expect(summarizeConditions(group([leaf("a"), leaf("b"), leaf("c")]))).toBe(
      "3 conditions",
    );
  });

  it("counts leaves across nested groups", () => {
    const nested = group([
      leaf("a"),
      group([leaf("b"), leaf("c")], GroupOperator.OR),
      leaf("d"),
    ]);
    expect(summarizeConditions(nested)).toBe("4 conditions");
  });

  it("counts leaves in deeply nested groups", () => {
    const deep = group([group([group([leaf("a"), leaf("b")])]), leaf("c")]);
    expect(summarizeConditions(deep)).toBe("3 conditions");
  });
});
