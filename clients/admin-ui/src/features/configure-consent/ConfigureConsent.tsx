import {
  Box,
  ButtonGroup,
  Center,
  Heading,
  List,
  ListItem,
  Spinner,
  Text,
  VStack,
} from "@fidesui/react";

import EmptyTableState from "~/features/common/table/EmptyTableState";
import { useGetAllSystemsQuery } from "~/features/system";

import AddCookie from "./AddCookie";
import AddVendor from "./AddVendor";

const AddButtons = () => (
  <ButtonGroup size="sm" colorScheme="primary">
    <AddVendor />
    <AddCookie />
  </ButtonGroup>
);

const EmptyStateContent = () => (
  <VStack spacing={4} alignItems="start">
    <Text>TODO</Text>
    <AddButtons />
  </VStack>
);

const ConfigureConsent = () => {
  const { data: allSystems, isLoading } = useGetAllSystemsQuery();

  if (isLoading) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }

  if (!allSystems || allSystems.length === 0) {
    return (
      <EmptyTableState
        title="No cookies or vendors have been added yet"
        description={<EmptyStateContent />}
      />
    );
  }

  return (
    // TODO(fides#4054): make this into a table
    <Box>
      <Heading size="md">Systems</Heading>
      <List>
        {allSystems.map((system) => (
          <ListItem key={system.fides_key}>{system.name}</ListItem>
        ))}
      </List>
      <AddButtons />
    </Box>
  );
};

export default ConfigureConsent;
