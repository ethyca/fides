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
import type { NextPage } from "next";
import React from "react";

import { StepperCircleCheckmarkIcon } from "~/features/common/Icon";
import {
  useGetAllSystemsQuery,
  useGetSystemByFidesKeyQuery,
} from "~/features/system/system.slice";

const SuccessPage: NextPage<{
  handleChangeStep: Function;
  handleChangeReviewStep: Function;
  systemFidesKey: string;
}> = ({ handleChangeStep, handleChangeReviewStep, systemFidesKey }) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemFidesKey);
  const { data: allRegisteredSystems } = useGetAllSystemsQuery();
  const filteredSystems = allRegisteredSystems?.filter(
    (system) => system.name !== existingSystem?.name
  );

  return (
    <chakra.form w="100%">
      <Stack ml="100px" spacing={10}>
        <Heading as="h3" color="green.500" size="lg">
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
            onClick={() => {
              handleChangeStep(4);
              handleChangeReviewStep(5);
            }}
            mr={2}
            size="sm"
            variant="outline"
          >
            Add next system
          </Button>
          <Button
            onClick={() => {
              handleChangeStep(5);
            }}
            colorScheme="primary"
            size="sm"
          >
            Continue
          </Button>
        </Box>
      </Stack>
    </chakra.form>
  );
};
export default SuccessPage;
