import { Badge, Box, HStack, Image, Text, Tooltip } from "fidesui";
import { QuestionIcon } from "fidesui";

interface VendorMatchBadgeProps {
  vendorName?: string | null;
  vendorLogoUrl?: string | null;
  confidence?: "high" | "medium" | "low" | null;
  isUnknown?: boolean;
}

export const VendorMatchBadge = ({
  vendorName,
  vendorLogoUrl,
  confidence,
  isUnknown = false,
}: VendorMatchBadgeProps) => {
  // Unknown vendor case
  if (isUnknown || !vendorName) {
    return (
      <Badge colorScheme="gray" variant="outline" fontSize="xs">
        <HStack spacing={1}>
          <QuestionIcon boxSize={3} />
          <Text>Unknown Vendor</Text>
        </HStack>
      </Badge>
    );
  }

  // Known vendor - color code by confidence
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
          {vendorLogoUrl && (
            <Image
              src={vendorLogoUrl}
            //   src={"https://impulso06.com/wp-content/uploads/2023/10/Guia-de-Tamanos-de-Imagenes-para-Publicar-en-Redes-Sociales-2023.png"}
              alt={vendorName}
              boxSize={4}
              objectFit="contain"
              fallback={<Box boxSize={4} />}
            />
          )}
          <Text>{vendorName}</Text>
        </HStack>
      </Badge>
    </Tooltip>
  );
};
