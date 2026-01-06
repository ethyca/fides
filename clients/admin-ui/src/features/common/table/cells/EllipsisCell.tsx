import { Typography } from "fidesui";
import { ReactNode } from "react";

interface EllipsisCellProps {
  /** The text content to display */
  children: ReactNode;
  /** Optional className to extend or overwrite the default width */
  className?: string;
  /** Whether to show a tooltip on hover. Defaults to true */
  tooltip?: boolean;
}

/**
 * A text component that truncates with ellipsis and shows a tooltip on hover.
 * Default width is w-36 (144px), but can be overridden with the className prop.
 *
 * @example
 * <EllipsisCell>Some very long text that will be truncated</EllipsisCell>
 *
 * @example
 * <EllipsisCell className="w-48">Custom width text</EllipsisCell>
 */
export const EllipsisCell = ({
  children,
  className = "w-36",
  tooltip = true,
}: EllipsisCellProps) => {
  if (!children) {
    return null;
  }

  return (
    <Typography.Text
      ellipsis={tooltip ? { tooltip: children } : true}
      className={className}
    >
      {children}
    </Typography.Text>
  );
};
