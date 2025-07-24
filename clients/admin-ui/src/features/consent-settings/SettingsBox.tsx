import { Box, BoxProps, Text } from "fidesui";
import { ReactNode } from "react";

const SettingsBox = ({
  title,
  children,
  ...props
}: { title: string; children: ReactNode } & BoxProps) => (
  <Box
    backgroundColor="var(--fidesui-bg-corinth)"
    borderRadius="4px"
    padding="3"
    data-testid={`setting-${title}`}
    {...props}
  >
    <Text
      as="h3"
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
