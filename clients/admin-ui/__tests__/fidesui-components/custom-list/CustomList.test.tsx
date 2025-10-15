import { fireEvent, render } from "@testing-library/react";
import { AntList as List } from "fidesui";

import { MOCK_LIST_DATA, TestDataItem } from "./mockListData";

// Reusable render function
const defaultRenderItem = (
  item: TestDataItem,
  index: number,
  checkbox?: React.ReactNode,
) => (
  <List.Item>
    <List.Item.Meta
      title={item.title}
      description={item.description}
      avatar={checkbox}
    />
  </List.Item>
);

describe("CustomList with rowSelection", () => {
  describe("Basic rendering", () => {
    it("renders list without rowSelection (no checkbox)", () => {
      const { getByText, container } = render(
        <List dataSource={MOCK_LIST_DATA} renderItem={defaultRenderItem} />,
      );

      expect(getByText("Item One")).toBeInTheDocument();
      expect(getByText("First item description")).toBeInTheDocument();
      // No checkboxes should be rendered
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes.length).toBe(0);
    });

    it("renders list with rowSelection enabled (checkbox provided)", () => {
      const { getByText, container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: [],
            onChange: jest.fn(),
          }}
          renderItem={defaultRenderItem}
        />,
      );

      expect(getByText("Item One")).toBeInTheDocument();
      // Checkboxes should be rendered
      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes.length).toBe(MOCK_LIST_DATA.length);
    });
  });

  describe("Selection state", () => {
    it("checkboxes reflect selectedRowKeys prop", () => {
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: ["1", "3"],
            onChange: jest.fn(),
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      // First checkbox (key "1") should be checked
      expect(checkboxes[0]).toBeChecked();
      // Second checkbox (key "2") should not be checked
      expect(checkboxes[1]).not.toBeChecked();
      // Third checkbox (key "3") should be checked
      expect(checkboxes[2]).toBeChecked();
    });

    it("supports multiple items being selected", () => {
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: ["1", "2", "3"],
            onChange: jest.fn(),
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes[0]).toBeChecked();
      expect(checkboxes[1]).toBeChecked();
      expect(checkboxes[2]).toBeChecked();
      expect(checkboxes[3]).not.toBeChecked();
      expect(checkboxes[4]).not.toBeChecked();
    });
  });

  describe("onChange callback", () => {
    it("calls onChange with updated keys when checkbox is clicked", () => {
      const handleChange = jest.fn();
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: [],
            onChange: handleChange,
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      fireEvent.click(checkboxes[0]);

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(["1"], [MOCK_LIST_DATA[0]]);
    });

    it("calls onChange with correct row objects when selecting multiple items", () => {
      const handleChange = jest.fn();
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: ["1"],
            onChange: handleChange,
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      // Click second checkbox to add to selection
      fireEvent.click(checkboxes[1]);

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(
        ["1", "2"],
        [MOCK_LIST_DATA[0], MOCK_LIST_DATA[1]],
      );
    });

    it("calls onChange when unchecking an item", () => {
      const handleChange = jest.fn();
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: ["1", "2"],
            onChange: handleChange,
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');
      // Uncheck first checkbox
      fireEvent.click(checkboxes[0]);

      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(["2"], [MOCK_LIST_DATA[1]]);
    });
  });

  describe("Disabled checkboxes", () => {
    it("handles disabled checkboxes correctly", () => {
      const handleChange = jest.fn();
      const { container } = render(
        <List
          dataSource={MOCK_LIST_DATA}
          rowSelection={{
            selectedRowKeys: [],
            onChange: handleChange,
            getCheckboxProps: (item) => ({
              disabled: item.locked,
            }),
          }}
          renderItem={defaultRenderItem}
        />,
      );

      const checkboxes = container.querySelectorAll('input[type="checkbox"]');

      // First three checkboxes should not be disabled
      expect(checkboxes[0]).not.toBeDisabled();
      expect(checkboxes[1]).not.toBeDisabled();
      expect(checkboxes[2]).not.toBeDisabled();
      // Fourth checkbox (locked item) should be disabled
      expect(checkboxes[3]).toBeDisabled();
      expect(checkboxes[4]).not.toBeDisabled();

      // Try to click the disabled checkbox (index 3 - locked item)
      fireEvent.click(checkboxes[3]);
      // onChange should not be called because checkbox is disabled
      expect(handleChange).not.toHaveBeenCalled();

      // Non-disabled checkboxes can still be toggled
      fireEvent.click(checkboxes[0]);
      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(["1"], [MOCK_LIST_DATA[0]]);
    });
  });
});
