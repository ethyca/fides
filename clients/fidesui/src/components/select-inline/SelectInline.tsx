import { Select } from "antd/lib";
import React, { ComponentProps, useState } from "react";

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
 * - Responsive tag display with expandable "Show more" functionality
 * - Case-insensitive filtering
 * - No tag creation allowed (only predefined options)
 * - Custom tag rendering with CustomTag components
 * - Add button positioned as prefix (hidden in readonly mode)
 * - Custom "+ X more" placeholder for overflow tags
 * - Readonly mode that disables editing and hides interactive elements
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
  maxTagPlaceholder,
  filterOption = (input, option) =>
    option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false,
  style = { width: "100%" },
  size = "small",
  prefix = <SelectInlinePrefix />,
  suffixIcon = null,
  className = "",
  readonly = false,
  tagRender = (props) => {
    const { label, closable, onClose } = props;
    return (
      <div className="mr-1">
        <AntTag
          color="white"
          closable={readonly ? false : closable}
          onClose={onClose}
        >
          {label}
        </AntTag>
      </div>
    );
  },
  ...props
}: SelectProps & { readonly?: boolean }) => {
  const [expanded, setExpanded] = useState(false);

  const customMaxTagPlaceholder =
    maxTagPlaceholder || ((omittedValues) => `+ ${omittedValues.length} more`);

  return (
    <Select
      mode={mode}
      variant={variant}
      showSearch={readonly ? false : showSearch}
      maxTagCount={expanded ? undefined : maxTagCount}
      maxTagPlaceholder={customMaxTagPlaceholder}
      filterOption={filterOption}
      style={style}
      size={size}
      prefix={readonly ? null : prefix}
      suffixIcon={suffixIcon}
      className={`${styles.selectInline} ${className}`}
      tagRender={tagRender}
      onClick={() => readonly && setExpanded(!expanded)}
      open={readonly ? false : undefined}
      {...props}
    />
  );
};
