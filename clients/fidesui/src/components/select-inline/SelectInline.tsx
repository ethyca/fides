import { Select } from "antd/lib";
import React, { ComponentProps, useState } from "react";

import { CustomTag as AntTag, CustomTypography } from "../../hoc";
import styles from "./SelectInline.module.scss";

type SelectProps = ComponentProps<typeof Select>;

type SelectInlineValue = string | number | boolean;

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
    <AntTag addable className="cursor-pointer m-0 border-none" />
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
  onTagClick,
  tagRender = (props) => {
    const { label, closable, onClose, value, isMaxTag } = props;

    if (isMaxTag) {
      return (
        <CustomTypography.Text className="block ml-1 text-xs">
          {label}
        </CustomTypography.Text>
      );
    }

    const handleTagClick = (e: React.MouseEvent) => {
      if (onTagClick) {
        e.stopPropagation();
        onTagClick(value, label);
      }
    };

    return (
      <div className="mr-1">
        <AntTag
          color="white"
          closable={readonly ? false : closable}
          onClose={onClose}
          onClick={onTagClick ? handleTagClick : undefined}
          className={onTagClick ? "cursor-pointer" : undefined}
        >
          {label}
        </AntTag>
      </div>
    );
  },
  ...props
}: SelectProps & {
  readonly?: boolean;
  onTagClick?: (value: SelectInlineValue, label: React.ReactNode) => void;
}) => {
  const [expanded, setExpanded] = useState(false);

  const handleExpandClick = (e: React.MouseEvent | React.KeyboardEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpanded(!expanded);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      handleExpandClick(e);
    }
  };

  const renderMaxTagPlaceholder: SelectProps["maxTagPlaceholder"] = (
    omittedValues,
  ) => {
    const count = omittedValues.length;

    if (readonly) {
      return (
        <span
          className="cursor-pointer"
          role="button"
          tabIndex={0}
          onClick={handleExpandClick}
          onKeyDown={handleKeyDown}
        >
          + {count} more
        </span>
      );
    }

    return <span>+ {count} more</span>;
  };

  const customMaxTagPlaceholder = maxTagPlaceholder || renderMaxTagPlaceholder;

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
      rootClassName={`${styles.selectInlineRoot} ${className}`}
      tagRender={tagRender}
      disabled={readonly}
      {...props}
    />
  );
};
