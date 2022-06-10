import { fireEvent, render } from "@testing-library/react";

import CheckboxTree from "~/features/common/CheckboxTree";

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
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={jest.fn()} />
    );
    expect(getByTestId("checkbox-grandparent")).toBeInTheDocument();
    expect(getByTestId("checkbox-great uncle")).toBeInTheDocument();
    expect(queryByTestId("checkbox-parent")).toBeNull();
    expect(queryByTestId("checkbox-child")).toBeNull();
    expect(queryByTestId("checkbox-sibling")).toBeNull();
  });

  it("can expand children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={jest.fn()} />
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
    const handleChecked = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={handleChecked} />
    );
    fireEvent.click(getByTestId("checkbox-grandparent"));
    expect(handleChecked).toBeCalledTimes(1);
    expect(handleChecked).toBeCalledWith(["grandparent"]);
  });

  it("can remove checked values", () => {
    const handleChecked = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        checked={["grandparent"]}
        onChecked={handleChecked}
      />
    );
    expect(getByTestId("checkbox-grandparent")).toHaveAttribute("data-checked");
    fireEvent.click(getByTestId("checkbox-grandparent"));
    expect(handleChecked).toBeCalledTimes(1);
    expect(handleChecked).toBeCalledWith([]);
  });

  it("can remove nested checked values", () => {
    const handleChecked = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        checked={[
          "grandparent",
          "grandparent.parent",
          "grandparent.parent.child",
          "great uncle",
        ]}
        onChecked={handleChecked}
      />
    );
    fireEvent.click(getByTestId("checkbox-grandparent"));
    expect(handleChecked).toBeCalledTimes(1);
    expect(handleChecked).toBeCalledWith(["great uncle"]);
  });

  it("can make ancestors checked when all descendants are checked", () => {
    const handleChecked = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={handleChecked} />
    );
    fireEvent.click(getByTestId("expand-grandparent"));
    fireEvent.click(getByTestId("checkbox-aunt"));
    expect(handleChecked).toBeCalledTimes(1);
    expect(handleChecked).toBeCalledWith(["grandparent.aunt"]);
    // expect(getByTestId("checkbox-grandparent")).toBeChecked();
  });

  it("can make ancestors indeterminate when some descendants are checked", () => {
    const handleChecked = jest.fn();
    const { getByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={handleChecked} />
    );
    fireEvent.click(getByTestId("expand-grandparent"));
    fireEvent.click(getByTestId("expand-parent"));
    fireEvent.click(getByTestId("checkbox-child"));
    expect(handleChecked).toBeCalledTimes(1);
    expect(handleChecked).toBeCalledWith(["child"]);
  });

  it("can render expanded when starting with checked child", () => {
    const { getByTestId } = render(
      <CheckboxTree
        nodes={MOCK_NODES}
        checked={["grandparent.parent.child"]}
        onChecked={jest.fn()}
      />
    );
    expect(getByTestId("checkbox-child")).toBeInTheDocument();
  });

  it("does not render an expanding arrow when node has no children", () => {
    const { getByTestId, queryByTestId } = render(
      <CheckboxTree nodes={MOCK_NODES} checked={[]} onChecked={jest.fn()} />
    );
    expect(getByTestId("expand-grandparent")).toBeInTheDocument();
    expect(queryByTestId("expand-great uncle")).toBeNull();
  });
});
