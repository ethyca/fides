import {
  AntTag as Tag,
  AntTagProps as TagProps,
  AntTooltip as Tooltip,
  CUSTOM_TAG_COLOR,
} from "fidesui";

interface TagCellProps extends TagProps {
  value: string;
  tooltip?: string;
  color?: CUSTOM_TAG_COLOR;
}

/**
 * A cell component that displays a tag with an optional tooltip
 */
const TagCell = ({ value, tooltip, color, ...tagProps }: TagCellProps) => {
  const innerTag = (
    <Tag color={color} data-testid="tag-cell" {...tagProps}>
      {value}
    </Tag>
  );

  if (!tooltip) {
    return innerTag;
  }

  return (
    <Tooltip title={tooltip}>
      {/* the span is necessary to prevent the tooltip from changing the line height */}
      <span>{innerTag}</span>
    </Tooltip>
  );
};

export default TagCell;
