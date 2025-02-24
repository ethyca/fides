import {
  AntTag as Tag,
  AntTagProps as TagProps,
  AntTooltip as Tooltip,
} from "fidesui";

import { formatDate } from "~/features/common/utils";

interface ResultStatusBadgeProps extends Omit<TagProps, "color"> {
  color: "success" | "error";
}

const ResultStatusBadge = ({ children, ...props }: ResultStatusBadgeProps) => {
  return <Tag {...props}>{children}</Tag>;
};

interface DiscoveryStatusBadgeCellProps {
  withConsent: boolean;
  dateDiscovered: string | null | undefined;
}

export const DiscoveryStatusBadgeCell = ({
  withConsent,
  dateDiscovered,
}: DiscoveryStatusBadgeCellProps) => {
  return (
    <Tooltip title={dateDiscovered ? formatDate(dateDiscovered) : undefined}>
      {/* tooltip throws errors if immediate child is not available or changes after render so this div wrapper helps keep it stable */}
      <div>
        {withConsent ? (
          <ResultStatusBadge color="success">With consent</ResultStatusBadge>
        ) : (
          <ResultStatusBadge color="error">Without consent</ResultStatusBadge>
        )}
      </div>
    </Tooltip>
  );
};
