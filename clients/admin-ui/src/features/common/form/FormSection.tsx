import { Box, BoxProps, Heading, Stack, Text } from "fidesui";

import { InfoTooltip } from "~/features/common/InfoTooltip";

const FormSection = ({
  title,
  tooltip,
  children,
  ...props
}: {
  title: string;
  tooltip?: string;
} & BoxProps) => (
  <Box borderRadius="md" border="1px solid" borderColor="gray.200" {...props}>
    <Heading
      as="h3"
      fontSize="sm"
      fontWeight="semibold"
      color="gray.700"
      py={4}
      px={6}
      backgroundColor="gray.50"
      borderRadius="md"
      textAlign="left"
    >
      {title}
      {tooltip ? (
        <Text as="span" mx={1}>
          <InfoTooltip label={tooltip} />
        </Text>
      ) : undefined}
    </Heading>
    <Stack p={6} spacing={6}>
      {children}
    </Stack>
  </Box>
);

export default FormSection;
