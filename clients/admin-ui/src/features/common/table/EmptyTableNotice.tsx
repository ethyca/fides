import { Text, VStack } from "fidesui";
import { ReactNode } from "react";

const EmptyTableNotice = ({
  title,
  description,
  button,
}: {
  title: string;
  description: string | ReactNode;
  button?: ReactNode;
}) => (
  <VStack
    mt={6}
    p={10}
    spacing={4}
    borderRadius="base"
    maxW="70%"
    data-testid="no-results-notice"
    alignSelf="center"
    margin="auto"
    textAlign="center"
  >
    <VStack>
      <Text fontSize="md" fontWeight="600">
        {title}
      </Text>
      <Text fontSize="sm">{description}</Text>
    </VStack>
    {button}
  </VStack>
);

export default EmptyTableNotice;
