import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useState } from "react";

import EditFieldDrawer from "./EditFieldDrawer";
import { DatasetField } from "./types";

interface Props {
  fields: DatasetField[];
}

const DatasetFieldsTable = ({ fields }: Props) => {
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
            <Th pl={0}>Field Name</Th>
            <Th pl={0}>Description</Th>
            <Th pl={0}>Identifiability</Th>
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
              <Td pl={0}>{field.name}</Td>
              <Td pl={0}>{field.description}</Td>
              <Td pl={0}>{field.data_qualifier}</Td>
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
