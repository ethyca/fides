import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useState } from "react";

import EditFieldDrawer from "./EditFieldDrawer";
import { ColumnMetadata, DatasetField } from "./types";

interface Props {
  fields: DatasetField[];
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ fields, columns }: Props) => {
  const [editDrawerIsOpen, setEditDrawerIsOpen] = useState(false);
  const [activeField, setActiveField] = useState<DatasetField | undefined>(
    undefined
  );
  const handleClose = () => {
    setEditDrawerIsOpen(false);
  };
  const handleClick = (field: DatasetField) => {
    setActiveField(field);
    setEditDrawerIsOpen(true);
  };
  return (
    <Box>
      <Table size="sm">
        <Thead>
          <Tr>
            {columns.map((c) => (
              <Th key={c.name} pl={0}>
                {c.name}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {fields.map((field) => (
            <Tr
              key={field.name}
              _hover={{ bg: "gray.50" }}
              cursor="pointer"
              onClick={() => handleClick(field)}
            >
              {columns.map((c) => (
                <Td key={`${field.name}-${field[c.attribute]}`} pl={0}>
                  {field[c.attribute]}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      {activeField && (
        <EditFieldDrawer
          isOpen={editDrawerIsOpen}
          onClose={handleClose}
          field={activeField}
        />
      )}
    </Box>
  );
};

export default DatasetFieldsTable;
