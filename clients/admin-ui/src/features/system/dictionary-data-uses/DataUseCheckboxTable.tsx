import { Checkbox, Table, Tag, Tbody, Td, Text, Th, Thead, Tr } from "fidesui";

import { DataUse } from "~/types/api";
import { DataUseDeclaration } from "~/types/dictionary-api";

interface Props {
  onChange: (dataUses: DataUseDeclaration[]) => void;
  allDataUses: DataUse[];
  dictDataUses: DataUseDeclaration[];
  checked: DataUseDeclaration[];
}

const DataUseCheckboxTable = ({
  onChange,
  allDataUses,
  dictDataUses,
  checked,
}: Props) => {
  const handleChangeAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onChange(dictDataUses);
    } else {
      onChange([]);
    }
  };

  const onCheck = (dataUse: DataUseDeclaration) => {
    const exists =
      checked.filter((du) => du.data_use === dataUse.data_use).length > 0;
    if (!exists) {
      const newChecked = [...checked, dataUse];
      onChange(newChecked);
    } else {
      const newChecked = checked.filter(
        (use) => use.data_use !== dataUse.data_use,
      );
      onChange(newChecked);
    }
  };

  const declarationTitle = (declaration: DataUseDeclaration) => {
    const dataUse = allDataUses.filter(
      (du) => du.fides_key === declaration.data_use,
    )[0];
    if (dataUse) {
      return dataUse.name;
    }
    return declaration.data_use;
  };

  const allChecked = dictDataUses.length === checked.length;

  return (
    <Table variant="unstyled" size="sm" border="1px" borderColor="gray.200">
      <Thead border="1px" borderColor="gray.200" backgroundColor="gray.50">
        <Tr>
          <Th width={3} borderRight="1px" borderRightColor="gray.200">
            <Checkbox
              py={2}
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
        {dictDataUses.map((du) => (
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
                backgroundColor="terracotta.500"
                fontWeight="semibold"
              >
                {declarationTitle(du)}
              </Tag>
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default DataUseCheckboxTable;
