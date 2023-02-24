import {
  Flex,
  Stack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import ClassifyResultsToggle from "common/ClassifyResultsToggle";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { SystemTableCell } from "~/features/common/SystemsCheckboxTable";
import ClassificationStatusBadge from "~/features/plus/ClassificationStatusBadge";
import { selectSystemClassifyInstanceMap } from "~/features/plus/plus.slice";
import { GenerateTypes, System } from "~/types/api";

import EditClassifySystemDrawer from "./EditClassifySystemDrawer";
import {
  selectActiveClassifySystem,
  setActiveClassifySystemFidesKey,
} from "./system.slice";

const ClassifySystemsTable = ({ systems }: { systems: System[] }) => {
  const dispatch = useAppDispatch();
  const classifyInstanceMap = useAppSelector(selectSystemClassifyInstanceMap);
  const activeSystem = useAppSelector(selectActiveClassifySystem);

  const handleClick = (system: System) => {
    dispatch(setActiveClassifySystemFidesKey(system.fides_key));
  };
  const [hideEmpty, setHideEmpty] = useState(false);

  return (
    <Stack>
      <Flex flexShrink={0} alignItems="center">
        <Text fontSize="xs" mr={2} size="sm">
          Only Show Findings
        </Text>
        <ClassifyResultsToggle hideEmpty={hideEmpty} onChange={setHideEmpty} />
      </Flex>
      <Table size="sm" data-testid="systems-classify-table">
        <Thead>
          <Tr>
            <Th>System Name</Th>
            <Th maxWidth="100px">Classification Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          {systems.map((system) => {
            const classifyInstance = classifyInstanceMap.get(system.fides_key);
            return (
              <Tr
                key={system.fides_key}
                data-testid={`row-${system.fides_key}`}
                _hover={{ bg: "gray.50" }}
                cursor="pointer"
                onClick={() => handleClick(system)}
                hidden={hideEmpty && !classifyInstance?.has_labels}
              >
                <Td>
                  <SystemTableCell system={system} attribute="name" />
                </Td>
                <Td data-testid={`status-${system.fides_key}`}>
                  <ClassificationStatusBadge
                    resource={GenerateTypes.SYSTEMS}
                    status={classifyInstance?.status}
                  />
                </Td>
              </Tr>
            );
          })}
        </Tbody>
      </Table>
      {activeSystem ? (
        <EditClassifySystemDrawer
          system={activeSystem}
          isOpen={activeSystem != null}
          onClose={() => dispatch(setActiveClassifySystemFidesKey(undefined))}
        />
      ) : null}
    </Stack>
  );
};

export default ClassifySystemsTable;
