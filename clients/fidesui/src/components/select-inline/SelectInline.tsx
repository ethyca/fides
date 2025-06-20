import { Select } from "antd/lib";
import { ComponentProps } from "react";

type SelectProps = ComponentProps<typeof Select>;

/**
 * SelectInline is a multi-select component wrapper around Ant Design's Select.
 * It provides consistent styling and behavior for inline multi-selection use cases.
 *
 * Default features:
 * - Multiple selection mode enabled
 * - Borderless variant for inline appearance
 * - Search functionality enabled
 * - Responsive tag display
 * - Case-insensitive filtering
 * - No tag creation allowed (only predefined options)
 */
export const SelectInline = ({
  mode = "multiple",
  variant = "borderless",
  showSearch = true,
  maxTagCount = "responsive",
  filterOption = (input, option) =>
    option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false,
  placeholder = "Select options...",
  style = { width: "100%" },
  ...props
}: SelectProps) => (
  <Select
    mode={mode}
    variant={variant}
    showSearch={showSearch}
    maxTagCount={maxTagCount}
    filterOption={filterOption}
    placeholder={placeholder}
    style={style}
    {...props}
  />
);
