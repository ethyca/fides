import { Select } from "antd/lib";
import React, { ComponentProps } from "react";

import { CustomTag as AntTag } from "../../hoc";
import styles from "./SelectInline.module.scss";

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
 * - Custom tag rendering with CustomTag components
 * - Add button positioned as prefix
 */

const SelectInlinePrefix = () => (
  <div style={{ paddingTop: "1px" }}>
    <AntTag addable color="white" className="cursor-pointer m-0 " />
  </div>
);

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
  prefix = <SelectInlinePrefix />,
  suffixIcon = null,
  className = "",
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
    prefix={prefix}
    suffixIcon={suffixIcon}
    className={`${styles.selectInline} ${className}`}
    tagRender={tagRender}
    {...props}
  />
);
