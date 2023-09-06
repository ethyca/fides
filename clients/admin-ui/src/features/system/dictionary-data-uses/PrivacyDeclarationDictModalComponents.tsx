import {
  Text,
  Table,
  TableContainer,
  Thead,
  Tr,
  Checkbox,
  Td,
  Tbody,
  Box,
  Stack,
  HStack,
  Button,
} from "@fidesui/react";
import { useState } from "react";
import { DataUse } from "../../../types/api";
import { SparkleIcon } from "../../common/Icon/SparkleIcon";
import DataUseCheckboxTable, { TempDataUse } from "./DataUseCheckboxTable";

interface Props {
  alreadyHasDataUses: boolean;
  onCancel: () => void;
  onAccept: (suggestions: TempDataUse[]) => void;
  vendorId?: string;
}

const PrivacyDeclarationDictModalComponents = ({
  alreadyHasDataUses,
  onCancel,
  onAccept,
  vendorId,
}: Props) => {
  const sampleData = [
    {
      name: "Data use 1",
      fides_key: "data_use_1",
    },
    {
      name: "Data use 2",
      fides_key: "data_use_2",
    },
    {
      name: "Data use 3",
      fides_key: "data_use_3",
    },
    {
      name: "Data use 4",
      fides_key: "data_use_4",
    },
    {
      name: "Data use 5",
      fides_key: "data_use_5",
    },
  ];

  const [selectedDataUses, setSelectedDataUses] =
    useState<TempDataUse[]>(sampleData);

  const handleChangeChecked = (newChecked: TempDataUse[]) => {
    setSelectedDataUses(newChecked);
  };

  return (
    <Stack spacing={4} mt={4}>
      <Box
        p={4}
        color="gray.700"
        backgroundColor="gray.50"
        border="1px"
        borderRadius={4}
        borderColor="purple.400"
      >
        <HStack alignItems="start" spacing={3}>
          <SparkleIcon color="purple.400" mt={2} />
          <Text>
            Fides has automatically generated the following data uses. These
            data uses are commonly assigned to this system type. You can accept
            these data use suggestions and optionally edit them or cancel and
            add data uses manually.
          </Text>
        </HStack>
      </Box>
      <TableContainer>
        <DataUseCheckboxTable
          allDataUses={sampleData}
          onChange={handleChangeChecked}
          checked={selectedDataUses}
        />
      </TableContainer>
      {alreadyHasDataUses ? (
        <Box
          p={4}
          color="gray.700"
          backgroundColor="red.50"
          border="1px"
          borderRadius={4}
          borderColor="red.200"
        >
          Please note, accepting these dictionary suggestions will override any
          data uses you have manually added or modified. For more help on this
          see our docs.
        </Box>
      ) : null}
      <HStack justifyContent="space-between">
        <Button onClick={onCancel}>Cancel</Button>
        <Button
          variant="primary"
          onClick={() => {
            onAccept(selectedDataUses);
          }}
          isDisabled={selectedDataUses.length === 0}
        >
          {selectedDataUses.length === sampleData.length
            ? "Accept all"
            : "Accept"}
        </Button>
      </HStack>
    </Stack>
  );
};

export default PrivacyDeclarationDictModalComponents;
