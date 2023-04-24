import { Box, Button, HStack, Text, WarningTwoIcon } from "@fidesui/react";
import NextLink from "next/link";
import { ReactNode } from "react";
import { UrlObject } from "url";

type Props = {
  title: string;
  description: string | ReactNode;
  buttonHref: string | UrlObject;
  buttonText: string;
};

const EmptyTableState = ({
  title,
  description,
  buttonHref,
  buttonText,
}: Props) => (
  <HStack
    backgroundColor="gray.50"
    border="1px solid"
    borderColor="blue.400"
    borderRadius="md"
    justifyContent="space-between"
    py={4}
    px={6}
    data-testid="empty-state"
  >
    <WarningTwoIcon alignSelf="start" color="blue.400" mt={0.5} />
    <Box>
      <Text fontWeight="bold" fontSize="sm" mb={1}>
        {title}
      </Text>

      <Text fontSize="sm" color="gray.600" lineHeight="5">
        {description}
      </Text>
    </Box>
    <Button size="sm" variant="outline" fontWeight="semibold" minWidth="auto">
      <NextLink href={buttonHref}>{buttonText}</NextLink>
    </Button>
  </HStack>
);

export default EmptyTableState;
