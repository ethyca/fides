import {
  Badge,
  Box,
  HStack,
  Image,
  QuestionIcon,
  Text,
  Tooltip,
} from "fidesui";

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
      <Badge colorScheme="gray" variant="outline" fontSize="xs">
        <HStack spacing={1}>
          <QuestionIcon boxSize={3} />
          <Text>Unknown Vendor</Text>
        </HStack>
      </Badge>
    );
  }

  const confidenceColors = {
    high: "green",
    medium: "yellow",
    low: "orange",
  };
  const colorScheme = confidence ? confidenceColors[confidence] : "gray";

  const tooltipLabel = confidence
    ? `Matched with ${confidence} confidence`
    : "Vendor matched";

  return (
    <Tooltip label={tooltipLabel} placement="top">
      <Badge colorScheme={colorScheme} fontSize="xs" px={2} py={1}>
        <HStack spacing={2}>
          {vendorLogoUrl ? (
            <Image
              src={vendorLogoUrl}
              alt={vendorName}
              boxSize={4}
              objectFit="contain"
              fallback={<Box boxSize={4} />}
            />
          ) : (
            <Box boxSize={4} />
          )}
          <Text>{vendorName}</Text>
        </HStack>
      </Badge>
    </Tooltip>
  );
};
