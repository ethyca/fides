import { AntFlex as Flex } from "fidesui";
import { ReactNode } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";

interface InfoCellProps {
  /** The text content */
  value: ReactNode;
  /** Tooltip text shown when hovering the info icon */
  tooltip: string;
}

/**
 * A cell component that displays text with an info tooltip icon.
 *
 * @example
 * <InfoCell
 *   value="Restrictions"
 *   tooltip="Restrictions control how vendors are permitted to process data."
 * />
 */
export const InfoCell = ({ value, tooltip }: InfoCellProps) => (
  <Flex align="center" gap="small">
    {value}
    <InfoTooltip label={tooltip} />
  </Flex>
);
