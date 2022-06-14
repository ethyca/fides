import { fireEvent, render } from "@testing-library/react";

import CheckboxTree, {
  getAncestorsAndCurrent,
  getDescendantsAndCurrent,
  getMostSpecificDescendants,
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
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />
    );
    expect(getByTestId("checkbox-grandparent")).toBeInTheDocument();
    expect(getByTestId("checkbox-great uncle")).toBeInTheDocument();
    expect(queryByTestId("checkbox-parent")).toBeNull();
    expect(queryByTestId("checkbox-child")).toBeNull();
    expect(queryByTestId("checkbox-sibling")).toBeNull();
  });

  it("can expand children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />
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
      />
    );
    fireEvent.click(getByTestId("checkbox-great uncle"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith(["great uncle"]);
  });

  it("can add nested checked values", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={[]}
        onSelected={handleSelected}
      />
    );
    fireEvent.click(getByTestId("checkbox-grandparent"));
    expect(handleSelected).toBeCalledTimes(1);
    // we only mark the most specific ones as "selected"
    expect(handleSelected).toBeCalledWith([
      "grandparent.parent.child",
      "grandparent.parent.sibling",
      "grandparent.aunt",
    ]);
  });

  it("can remove checked values", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["great uncle"]}
        onSelected={handleSelected}
      />
    );
    expect(
      getByTestId("checkbox-great uncle").querySelector("span")
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
      />
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
      />
    );
    fireEvent.click(getByTestId("checkbox-child"));
    expect(handleSelected).toBeCalledTimes(1);
    expect(handleSelected).toBeCalledWith(["great uncle"]);
  });

  it("can render children as selected when a parent is selected", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent"]}
        onSelected={handleSelected}
      />
    );
    expect(
      getByTestId("checkbox-grandparent").querySelector("span")
    ).toHaveAttribute("data-checked");
    expect(
      getByTestId("checkbox-parent").querySelector("span")
    ).toHaveAttribute("data-checked");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked"
    );
  });

  it("can render ancestors indeterminate when some descendants are checked", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child"]}
        onSelected={handleSelected}
      />
    );

    expect(
      getByTestId("checkbox-grandparent").querySelector("span")
    ).toHaveAttribute("data-indeterminate");
    expect(
      getByTestId("checkbox-parent").querySelector("span")
    ).toHaveAttribute("data-indeterminate");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked"
    );
  });

  it("can render ancestors checked when all descendants are checked", () => {
    const handleSelected = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child", "grandparent.parent.sibling"]}
        onSelected={handleSelected}
      />
    );
    expect(
      getByTestId("checkbox-grandparent").querySelector("span")
    ).toHaveAttribute("data-indeterminate");
    expect(
      getByTestId("checkbox-parent").querySelector("span")
    ).toHaveAttribute("data-checked");
    expect(getByTestId("checkbox-child").querySelector("span")).toHaveAttribute(
      "data-checked"
    );
    expect(
      getByTestId("checkbox-sibling").querySelector("span")
    ).toHaveAttribute("data-checked");
  });

  it("can render expanded when starting with checked child", () => {
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        selected={["grandparent.parent.child"]}
        onSelected={jest.fn()}
      />
    );
    expect(getByTestId("checkbox-child")).toBeInTheDocument();
  });

  it("does not render an expanding arrow when node has no children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} selected={[]} onSelected={jest.fn()} />
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

    it("can get most specific descendants", () => {
      expect(getMostSpecificDescendants(["grandparent"])).toEqual([
        "grandparent",
      ]);
      expect(
        getMostSpecificDescendants(["grandparent", "grandparent.parent"])
      ).toEqual(["grandparent.parent"]);
      expect(
        getMostSpecificDescendants([
          "grandparent",
          "grandparent.parent",
          "grandparent.parent.child",
        ])
      ).toEqual(["grandparent.parent.child"]);
      expect(
        getMostSpecificDescendants([
          "grandparent",
          "grandparent.parent",
          "grandparent.aunt",
        ])
      ).toEqual(["grandparent.parent", "grandparent.aunt"]);
    });

    it("can get all descendants of a node", () => {
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent")
          .map((d) => d.value)
          .sort()
      ).toEqual(
        [
          "grandparent",
          "grandparent.parent",
          "grandparent.parent.child",
          "grandparent.parent.sibling",
          "grandparent.aunt",
        ].sort()
      );
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent.parent")
          .map((d) => d.value)
          .sort()
      ).toEqual(
        [
          "grandparent.parent",
          "grandparent.parent.child",
          "grandparent.parent.sibling",
        ].sort()
      );
      expect(
        getDescendantsAndCurrent(MOCK_NODES, "grandparent.parent.child").map(
          (d) => d.value
        )
      ).toEqual(["grandparent.parent.child"]);
    });
  });
});
