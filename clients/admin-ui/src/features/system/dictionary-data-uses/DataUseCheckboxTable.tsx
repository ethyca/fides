import {
  Checkbox,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
} from "@fidesui/react";
import { DataUse } from "../../../types/api";

// interface Props {
//   onChange: (dataUses: DataUse[]) => void;
//   allDataUses: DataUse[];
//   checked: DataUse[];
// }

export type TempDataUse = {
  name: string;
  fides_key: string;
};

interface TempProps {
  onChange: (dataUses: TempDataUse[]) => void;
  allDataUses: TempDataUse[];
  checked: TempDataUse[];
}

const DataUseCheckboxTable = ({
  onChange,
  allDataUses,
  checked,
}: TempProps) => {
  const handleChangeAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onChange(allDataUses);
    } else {
      onChange([]);
    }
  };

  const onCheck = (dataUse: TempDataUse) => {
    const exists =
      checked.filter((du) => du.fides_key === dataUse.fides_key).length > 0;
    console.log(exists);
    if (!exists) {
      const newChecked = [...checked, dataUse];
      onChange(newChecked);
    } else {
      const newChecked = checked.filter(
        (use) => use.fides_key !== dataUse.fides_key
      );
      onChange(newChecked);
    }
  };

  const tableHeaderProps = {
    border: "1px",
    borderColor: "gray.200",
    backgroundColor: "gray.50",
  };

  const tableHeaderTextProps = {
    fontSize: "12px",
    fontWeight: "500",
    casing: "none",
    letterSpacing: "0",
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
          <Tr key={du.fides_key} border="1px" borderColor="gray.200">
            <Td borderRight="1px" borderRightColor="gray.200">
              <Checkbox
                colorScheme="complimentary"
                value={du.fides_key}
                isChecked={
                  checked.filter((use) => use.fides_key === du.fides_key)
                    .length > 0
                }
                onChange={() => onCheck(du)}
                data-testid={`checkbox-${du.fides_key}`}
              />
            </Td>
            <Td>{du.name}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default DataUseCheckboxTable;
