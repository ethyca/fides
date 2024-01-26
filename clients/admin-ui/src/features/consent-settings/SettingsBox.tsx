import { Box, BoxProps, Text } from "@fidesui/react";
import { ReactNode } from "react";

const SettingsBox = ({
  title,
  children,
  ...props
}: { title: string; children: ReactNode } & BoxProps) => (
  <Box
    backgroundColor="gray.50"
    borderRadius="4px"
    padding="3"
    data-testid={`setting-${title}`}
    {...props}
  >
    <Text
      fontSize="md"
      fontWeight="bold"
      lineHeight={5}
      color="gray.700"
      mb={3}
    >
      {title}
    </Text>
    {children}
  </Box>
);

export default SettingsBox;
