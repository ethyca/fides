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
import { useEffect, useState } from "react";
import { useAppSelector } from "../../../app/hooks";
import {
  selectDictDataUses,
  useGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import { SparkleIcon } from "../../common/Icon/SparkleIcon";
import DataUseCheckboxTable from "./DataUseCheckboxTable";
import { DictDataUse } from "../../plus/types";

interface Props {
  alreadyHasDataUses: boolean;
  onCancel: () => void;
  onAccept: (suggestions: DictDataUse[]) => void;
  vendorId: number;
}

const PrivacyDeclarationDictModalComponents = ({
  alreadyHasDataUses,
  onCancel,
  onAccept,
  vendorId,
}: Props) => {
  const [selectedDataUses, setSelectedDataUses] = useState<DictDataUse[]>([]);

  useGetDictionaryDataUsesQuery({ vendor_id: vendorId });
  const dictDataUses = useAppSelector(selectDictDataUses(vendorId));

  useEffect(() => {
    setSelectedDataUses(dictDataUses);
  }, [dictDataUses]);

  console.log(dictDataUses);

  const handleChangeChecked = (newChecked: DictDataUse[]) => {
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
          allDataUses={dictDataUses}
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
          {selectedDataUses.length === dictDataUses.length
            ? "Accept all"
            : "Accept"}
        </Button>
      </HStack>
    </Stack>
  );
};

export default PrivacyDeclarationDictModalComponents;
