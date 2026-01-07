import {
  Avatar,
  Flex,
  Icons,
  Tag,
  TagProps,
  Tooltip,
  Typography,
} from "fidesui";

const { Text } = Typography;

const CONFIDENCE_COLORS: Record<
  NonNullable<VendorMatchBadgeProps["confidence"]>,
  TagProps["color"]
> = {
  high: "success",
  medium: "warning",
  low: "alert",
};

interface VendorMatchBadgeProps {
  vendorName?: string | null;
  vendorLogoUrl?: string | null;
  confidence?: "high" | "medium" | "low" | null;
}

export const VendorMatchBadge = ({
  vendorName,
  vendorLogoUrl,
  confidence,
}: VendorMatchBadgeProps) => {
  if (!vendorName) {
    return (
      <Tag>
        <Flex align="center" gap="small">
          <Icons.Help size={12} />
          <Text>Unknown vendor</Text>
        </Flex>
      </Tag>
    );
  }

  const color = confidence ? CONFIDENCE_COLORS[confidence] : undefined;
  const tooltipTitle = confidence
    ? `Matched with ${confidence} confidence`
    : "Vendor matched";

  return (
    <Tooltip title={tooltipTitle}>
      <Tag color={color}>
        <Flex align="center" gap="small">
          <Avatar size={18} src={vendorLogoUrl ?? undefined} alt={vendorName}>
            {vendorName.charAt(0)?.toUpperCase()}
          </Avatar>
          <Text>{vendorName}</Text>
        </Flex>
      </Tag>
    </Tooltip>
  );
};
