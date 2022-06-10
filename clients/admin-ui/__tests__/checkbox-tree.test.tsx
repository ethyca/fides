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
    expect(queryByTestId("parent")).toBeNull();
    expect(queryByTestId("child")).toBeNull();
    expect(queryByTestId("sibling")).toBeNull();
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
    expect(queryByTestId("child")).toBeNull();
    expect(queryByTestId("sibling")).toBeNull();
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

  it("can make ancestors checked", () => {});

  it("can make ancestors indeterminate", () => {});

  it("can render expanded when starting with checked child", () => {});
});
