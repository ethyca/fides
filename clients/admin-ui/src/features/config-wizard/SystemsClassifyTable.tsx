import { Button, Stack, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";

import { selectSystemsForReview } from "./config-wizard.slice";

const SystemsClassifyTable = ({ onFinish }: { onFinish: () => void }) => {
  const systems = useAppSelector(selectSystemsForReview);
  return (
    <Stack>
      <Table size="sm" data-testid="systems-classify-table">
        <Thead>
          <Tr>
            <Th>System Name</Th>
            <Th>Description</Th>
          </Tr>
        </Thead>
        <Tbody>
          {systems.map((system) => (
            <Tr key={system.fides_key}>
              <Td>{system.name}</Td>
              <Td>{system.description}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      <Button colorScheme="primary" onClick={onFinish}>
        Finish
      </Button>
    </Stack>
  );
};

export default SystemsClassifyTable;
