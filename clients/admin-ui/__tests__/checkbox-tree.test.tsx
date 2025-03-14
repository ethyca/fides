import { fireEvent, render } from "@testing-library/react";

import CheckboxTree, {
  ancestorIsSelected,
  getAncestorsAndCurrent,
  getDescendantsAndCurrent,
} from "~/features/common/CheckboxTree";

const MOCK_NODES = [
  {
    label: "grandparent",
    value: "grandparent",
    children: [
      {
        label: "parent",
        value: "grandparent.parent",
        children: [
          { label: "child", value: "grandparent.parent.child", children: [] },
          {
            label: "sibling",
            value: "grandparent.parent.sibling",
            children: [],
          },
        ],
      },
      {
        label: "aunt",
        value: "grandparent.aunt",
        children: [],
      },
      {
        label: "aunt_second",
        value: "grandparent.aunt_second",
        children: [],
      },
    ],
  },
  {
    label: "great uncle",
    value: "great uncle",
    children: [],
  },
];

describe("Checkbox tree", () => {
  it("renders just the top level nodes when none are selected", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />,
    );
    expect(getByTestId("checkbox-grandparent")).toBeInTheDocument();
    expect(getByTestId("checkbox-great uncle")).toBeInTheDocument();
    expect(queryByTestId("checkbox-parent")).toBeNull();
    expect(queryByTestId("checkbox-child")).toBeNull();
    expect(queryByTestId("checkbox-sibling")).toBeNull();
  });

  it("can expand children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />,
    );
    expect(queryByTestId("checkbox-parent")).toBeNull();
    fireEvent.click(getByTestId("expand-grandparent"));
    expect(getByTestId("checkbox-grandparent")).toBeInTheDocument();
    expect(getByTestId("checkbox-great uncle")).toBeInTheDocument();
    expect(getByTestId("checkbox-parent")).toBeInTheDocument();
    expect(getByTestId("checkbox-aunt")).toBeInTheDocument();
    expect(queryByTestId("checkbox-child")).toBeNull();
    expect(queryByTestId("checkbox-sibling")).toBeNull();
  });

  it("can add checked values", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={[]}
        onSelected={handleSelected}
      />,
    );
    fireEvent.click(getByTestId("checkbox-great uncle"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith(["great uncle"]);
  });

  it("can remove checked values", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["great uncle"]}
        onSelected={handleSelected}
      />,
    );
    expect(
      getByTestId("checkbox-great uncle").querySelector("span"),
    ).toHaveAttribute("data-checked");
    fireEvent.click(getByTestId("checkbox-great uncle"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith([]);
  });

  it("can remove nested checked values", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={[
          "grandparent",
          "grandparent.parent",
          "grandparent.parent.child",
          "great uncle",
        ]}
        onSelected={handleSelected}
      />,
    );
    fireEvent.click(getByTestId("checkbox-grandparent"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith(["great uncle"]);
  });

  it("can remove ancestors when no descendants are selected", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child", "great uncle"]}
        onSelected={handleSelected}
      />,
    );
    fireEvent.click(getByTestId("checkbox-child"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith(["great uncle"]);
  });

  it("can render children as selected and disabled when a parent is selected", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent"]}
        onSelected={handleSelected}
      />,
    );
    expect(
      getByTestId("checkbox-grandparent").querySelector("span"),
    ).toHaveAttribute("data-checked");
    expect(
      getByTestId("checkbox-parent").querySelector("span"),
    ).toHaveAttribute("data-checked");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked",
    );
    expect(getByTestId("checkbox-grandparent")).not.toHaveAttribute(
      "data-disabled",
    );
    expect(getByTestId("checkbox-child")).toHaveAttribute("data-disabled");
  });

  it("can render ancestors indeterminate when some descendants are checked", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child"]}
        onSelected={handleSelected}
      />,
    );

    expect(
      getByTestId("checkbox-grandparent").querySelector("span"),
    ).toHaveAttribute("data-indeterminate");
    expect(
      getByTestId("checkbox-parent").querySelector("span"),
    ).toHaveAttribute("data-indeterminate");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked",
    );
  });

  it("can render ancestors checked when all descendants are checked", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child", "grandparent.parent.sibling"]}
        onSelected={handleSelected}
      />,
    );
    expect(
      getByTestId("checkbox-grandparent").querySelector("span"),
    ).toHaveAttribute("data-indeterminate");
    expect(
      getByTestId("checkbox-parent").querySelector("span"),
    ).toHaveAttribute("data-checked");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked",
    );
    expect(
      getByTestId("checkbox-sibling").querySelector("span"),
    ).toHaveAttribute("data-checked");
  });

  it("can render expanded when starting with checked child", () => {
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child"]}
        onSelected={jest.fn()}
      />,
    );
    expect(getByTestId("checkbox-child")).toBeInTheDocument();
  });

  it("does not render an expanding arrow when node has no children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />,
    );
    expect(getByTestId("expand-grandparent")).toBeInTheDocument();
    expect(queryByTestId("expand-great uncle")).toBeNull();
  });

  describe("checkbox util functions", () => {
    it("can get ancestors", () => {
      expect(getAncestorsAndCurrent("grandparent")).toEqual(["grandparent"]);
      expect(getAncestorsAndCurrent("grandparent.parent.child")).toEqual([
        "grandparent",
        "grandparent.parent",
        "grandparent.parent.child",
      ]);
    });

    it("can get all descendants of a node", () => {
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent")
          .map((d) => d.value)
          .sort(),
      ).toEqual(
        [
          "grandparent",
          "grandparent.parent",
          "grandparent.parent.child",
          "grandparent.parent.sibling",
          "grandparent.aunt",
          "grandparent.aunt_second",
        ].sort(),
      );
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent.parent")
          .map((d) => d.value)
          .sort(),
      ).toEqual(
        [
          "grandparent.parent",
          "grandparent.parent.child",
          "grandparent.parent.sibling",
        ].sort(),
      );
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent.parent.child").map(
          (d) => d.value,
        ),
      ).toEqual(["grandparent.parent.child"]);

      // make sure aunt_second does not sneak in
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent.aunt").map(
          (d) => d.value,
        ),
      ).toEqual(["grandparent.aunt"]);
    });

    it("can determine if an ancestor is selected", () => {
      expect(
        ancestorIsSelected(["grandparent"], "grandparent.parent"),
      ).toBeTruthy();
      expect(ancestorIsSelected(["grandparent"], "great uncle")).toBeFalsy();
      expect(
        ancestorIsSelected(["grandparent"], "grandparent.parent.child"),
      ).toBeTruthy();
      expect(
        ancestorIsSelected(["grandparent.parent"], "grandparent.parent.child"),
      ).toBeTruthy();
      expect(ancestorIsSelected(["grandparent"], "grandparent")).toBeFalsy();
    });
  });
});
