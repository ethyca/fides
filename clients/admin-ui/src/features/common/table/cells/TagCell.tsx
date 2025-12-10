import {
  AntTag as Tag,
  AntTooltip as Tooltip,
  CUSTOM_TAG_COLOR,
} from "fidesui";

/**
 * A cell component that displays a tag with an optional tooltip.
 *
 * @param value - The value to display in the tag
 * @param tooltip - The tooltip to display when hovering over the tag
 * @param color - The color of the tag
 */
const TagCell = ({
  value,
  tooltip,
  color,
}: {
  value: string;
  tooltip: string;
  color: CUSTOM_TAG_COLOR;
}) => {
  const innerTag = (
    <Tag color={color} data-testid="tag-cell">
      {value}
    </Tag>
  );
  if (tooltip) {
    return (
      <Tooltip title={tooltip}>
        {/* the span is necessary to prevent the tooltip from changing the line height */}
        <span>{innerTag}</span>
      </Tooltip>
    );
  }
  return innerTag;
};

export default TagCell;
