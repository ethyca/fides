import { Select } from "antd/lib";
import { ComponentProps } from "react";

import { CustomTag as AntTag } from "../../hoc";

type SelectProps = ComponentProps<typeof Select>;

/**
 * SelectInline is a multi-select component wrapper around Ant Design's Select.
 * It provides consistent styling and behavior for inline multi-selection use cases.
 * It will usually be used in a table cell.
 *
 * Default features:
 * - Multiple selection mode enabled
 * - Borderless variant for inline appearance
 * - Search functionality enabled
 * - Responsive tag display
 * - Case-insensitive filtering
 * - No tag creation allowed (only predefined options)
 * - Custom tag rendering with small CustomTag components
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
  size = "small",
  tagRender = (props) => {
    const { label, closable, onClose } = props;
    return (
      <div className="mr-1">
        <AntTag color="white" closable={closable} onClose={onClose}>
          {label}
        </AntTag>
      </div>
    );
  },
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
    size={size}
    tagRender={tagRender}
    {...props}
  />
);
