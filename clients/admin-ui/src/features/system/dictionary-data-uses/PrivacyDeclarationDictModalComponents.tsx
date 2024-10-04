import { AntButton, Box, HStack, Stack, TableContainer, Text } from "fidesui";
import { useEffect, useState } from "react";

import {
  selectDictDataUses,
  useGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import { DataUseDeclaration } from "~/types/dictionary-api";

import { useAppSelector } from "../../../app/hooks";
import { DataUse } from "../../../types/api";
import { SparkleIcon } from "../../common/Icon/SparkleIcon";
import DataUseCheckboxTable from "./DataUseCheckboxTable";

interface Props {
  alreadyHasDataUses: boolean;
  allDataUses: DataUse[];
  onCancel: () => void;
  onAccept: (suggestions: DataUseDeclaration[]) => void;
  vendorId: string;
}

const PrivacyDeclarationDictModalComponents = ({
  alreadyHasDataUses,
  allDataUses,
  onCancel,
  onAccept,
  vendorId,
}: Props) => {
  const [selectedDataUses, setSelectedDataUses] = useState<
    DataUseDeclaration[]
  >([]);

  useGetDictionaryDataUsesQuery({ vendor_id: vendorId });
  const dictDataUses = useAppSelector(selectDictDataUses(vendorId));

  useEffect(() => {
    setSelectedDataUses(dictDataUses);
  }, [dictDataUses]);

  const handleChangeChecked = (newChecked: DataUseDeclaration[]) => {
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
      <TableContainer maxHeight={96} overflowY="scroll">
        <DataUseCheckboxTable
          dictDataUses={dictDataUses}
          allDataUses={allDataUses}
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
        <AntButton onClick={onCancel}>Cancel</AntButton>
        <AntButton
          type="primary"
          onClick={() => {
            onAccept(selectedDataUses);
          }}
          disabled={selectedDataUses.length === 0}
        >
          {selectedDataUses.length === dictDataUses.length
            ? "Accept all"
            : "Accept"}
        </AntButton>
      </HStack>
    </Stack>
  );
};

export default PrivacyDeclarationDictModalComponents;
