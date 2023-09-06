import {
  Checkbox,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
  Tag,
} from "@fidesui/react";
import { useEffect } from "react";
import { DictDataUse } from "../../plus/types";

interface Props {
  onChange: (dataUses: DictDataUse[]) => void;
  allDataUses: DictDataUse[];
  checked: DictDataUse[];
}

const DataUseCheckboxTable = ({ onChange, allDataUses, checked }: Props) => {
  const handleChangeAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onChange(allDataUses);
    } else {
      onChange([]);
    }
  };

  const onCheck = (dataUse: DictDataUse) => {
    const exists =
      checked.filter((du) => du.data_use === dataUse.data_use).length > 0;
    if (!exists) {
      const newChecked = [...checked, dataUse];
      onChange(newChecked);
    } else {
      const newChecked = checked.filter(
        (use) => use.data_use !== dataUse.data_use
      );
      onChange(newChecked);
    }
  };

  const tableHeaderProps = {
    border: "1px",
    borderColor: "gray.200",
    backgroundColor: "gray.50",
  };

  const allChecked = allDataUses.length === checked.length;

  return (
    <Table variant="unstyled">
      <Thead {...tableHeaderProps}>
        <Tr>
          <Th width={3} borderRight="1px" borderRightColor="gray.200">
            <Checkbox
              colorScheme="complimentary"
              isChecked={allChecked}
              onChange={handleChangeAll}
              data-testid="select-all"
            />
          </Th>
          <Th>
            <Text
              fontSize="md"
              fontWeight="500"
              casing="none"
              letterSpacing={0}
            >
              Data use
            </Text>
          </Th>
        </Tr>
      </Thead>
      <Tbody>
        {allDataUses.map((du) => (
          <Tr key={du.data_use} border="1px" borderColor="gray.200">
            <Td borderRight="1px" borderRightColor="gray.200">
              <Checkbox
                colorScheme="complimentary"
                value={du.data_use}
                isChecked={
                  checked.filter((use) => use.data_use === du.data_use).length >
                  0
                }
                onChange={() => onCheck(du)}
                data-testid={`checkbox-${du.data_use}`}
              />
            </Td>
            <Td>
              <Tag
                size="lg"
                py={1}
                color="white"
                backgroundColor="purple.500"
                fontWeight="semibold"
              >
                {du.data_use}
              </Tag>
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default DataUseCheckboxTable;
