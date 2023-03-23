import {
  Badge,
  Box,
  Button,
  chakra,
  Heading,
  Stack,
  StepperCircleCheckmarkIcon,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import { useRouter } from "next/router";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { SYSTEM_ROUTE } from "~/constants";
import {
  selectAllSystems,
  setActiveSystem,
} from "~/features/system/system.slice";
import { System } from "~/types/api";

interface Props {
  system: System;
  onAddNextSystem: () => void;
}
const SystemRegisterSuccess = ({ system, onAddNextSystem }: Props) => {
  const allRegisteredSystems = useAppSelector(selectAllSystems);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const otherSystems = allRegisteredSystems
    ? allRegisteredSystems.filter(
        (registeredSystem) => registeredSystem.name !== system.name
      )
    : [];

  const systemName = system.name ?? system.fides_key;

  const onFinish = () => {
    dispatch(setActiveSystem(undefined));

    router.push(SYSTEM_ROUTE);
  };

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
              <Tr>
                <Td color="green.500">{systemName}</Td>
                <Td>
                  <StepperCircleCheckmarkIcon boxSize={5} />
                </Td>
              </Tr>
              {otherSystems.map((s) => (
                <Tr key={`${s.fides_key}-tr`}>
                  <Td>{s.name}</Td>
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
            onClick={onFinish}
            colorScheme="primary"
            size="sm"
            data-testid="finish-btn"
          >
            Finish
          </Button>
        </Box>
      </Stack>
    </chakra.form>
  );
};
export default SystemRegisterSuccess;
