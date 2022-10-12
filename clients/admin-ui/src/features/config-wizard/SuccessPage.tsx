import {
  Badge,
  Box,
  Button,
  chakra,
  Heading,
  Stack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import React from "react";

import {
  StepperCircleCheckmarkIcon,
  StepperCircleIcon,
} from "~/features/common/Icon";
import { System } from "~/types/api";

interface Props {
  systemInReview: System;
  systemsForReview: System[];
  onContinue: () => void;
  onAddNextSystem: () => void;
}
const SuccessPage = ({
  systemInReview,
  systemsForReview,
  onAddNextSystem,
  onContinue,
}: Props) => {
  const systemName = systemInReview.name ?? systemInReview.fides_key;

  // Systems are reviewed in order, so a lower index means that system has been reviewed
  // and a higher index means they'll reviewed after hitting "next".
  const systemInReviewIndex = systemsForReview.findIndex(
    (s) => s.fides_key === systemInReview.fides_key
  );

  return (
    <chakra.form w="100%">
      <Stack spacing={10}>
        <Heading
          as="h3"
          color="green.500"
          size="lg"
          data-testid="success-page-heading"
        >
          <Badge
            fontSize="16px"
            margin="10px"
            padding="10px"
            variant="solid"
            colorScheme="green"
          >
            Success
          </Badge>
          {systemName} successfully registered!
        </Heading>
        <Text>{systemName} has been successfully added to the registry!</Text>
        <TableContainer>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th pl={0}>System Name</Th>
              </Tr>
            </Thead>
            <Tbody>
              {systemsForReview.map((s, i) => (
                <Tr key={`${s.fides_key}-tr`}>
                  <Td
                    color={i === systemInReviewIndex ? "green.500" : undefined}
                  >
                    {s.name}
                  </Td>
                  <Td>
                    {i <= systemInReviewIndex ? (
                      <StepperCircleCheckmarkIcon boxSize={5} />
                    ) : (
                      <StepperCircleIcon boxSize={5} />
                    )}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>

        <Text>You can continue to add more systems now or finish.</Text>

        <Box>
          <Button
            onClick={onAddNextSystem}
            mr={2}
            size="sm"
            variant="outline"
            data-testid="add-next-system-btn"
          >
            Add system manually
          </Button>

          <Button
            onClick={onContinue}
            colorScheme="primary"
            size="sm"
            data-testid="continue-btn"
          >
            Continue
          </Button>
        </Box>
      </Stack>
    </chakra.form>
  );
};
export default SuccessPage;
