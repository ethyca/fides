import { Box, BoxProps, Heading, Stack, Text } from "fidesui";

import QuestionTooltip from "~/features/common/QuestionTooltip";

const FormSection = ({
  title,
  tooltip,
  children,
  ...props
}: {
  title: string;
  tooltip?: string;
} & BoxProps) => (
  <Box
    borderRadius="md"
    border="1px solid"
    borderColor="neutral.200"
    {...props}
  >
    <Heading
      as="h3"
      fontSize="sm"
      fontWeight="semibold"
      color="neutral.700"
      py={4}
      px={6}
      backgroundColor="neutral.50"
      borderRadius="md"
      textAlign="left"
    >
      {title}
      {tooltip ? (
        <Text as="span" mx={1}>
          <QuestionTooltip label={tooltip} />
        </Text>
      ) : undefined}
    </Heading>
    <Stack p={6} spacing={6}>
      {children}
    </Stack>
  </Box>
);

export default FormSection;
