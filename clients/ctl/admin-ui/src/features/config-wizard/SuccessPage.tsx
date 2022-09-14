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

import { StepperCircleCheckmarkIcon } from "~/features/common/Icon";
import {
  useGetAllSystemsQuery,
  useGetSystemByFidesKeyQuery,
} from "~/features/system/system.slice";
import { System } from "~/types/api";

interface Props {
  systemKey: System["fides_key"];
  onContinue: () => void;
  onAddNextSystem: () => void;
}
const SuccessPage = ({ systemKey, onAddNextSystem, onContinue }: Props) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemKey);
  const { data: allRegisteredSystems } = useGetAllSystemsQuery();
  const filteredSystems = allRegisteredSystems?.filter(
    (system) => system.name !== existingSystem?.name
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
          {existingSystem?.name} successfully registered!
        </Heading>
        <Text>
          {existingSystem?.name} has been successfully added to the registry!
        </Text>
        <TableContainer>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th pl={0}>System Name</Th>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td color="green.500">{existingSystem?.name}</Td>
                <Td>
                  <StepperCircleCheckmarkIcon boxSize={5} />
                </Td>
              </Tr>
              {filteredSystems?.map((system) => (
                <Tr key={`${system.name}-tr`}>
                  <Td key={system.name}>{system.name}</Td>
                  <Td>
                    <StepperCircleCheckmarkIcon boxSize={5} />
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
            Add next system
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
