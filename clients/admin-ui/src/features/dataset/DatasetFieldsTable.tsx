import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import DataCategoryTag from "../taxonomy/DataCategoryTag";
import IdentifiabilityTag from "../taxonomy/IdentifiabilityTag";
import { selectActiveFieldIndex, setActiveFieldIndex } from "./dataset.slice";
import EditFieldDrawer from "./EditFieldDrawer";
import { ColumnMetadata, DatasetField } from "./types";

interface Props {
  fields: DatasetField[];
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ fields, columns }: Props) => {
  const dispatch = useDispatch();
  const [editDrawerIsOpen, setEditDrawerIsOpen] = useState(false);
  const activeFieldIndex = useSelector(selectActiveFieldIndex);

  const handleClose = () => {
    setEditDrawerIsOpen(false);
    dispatch(setActiveFieldIndex(null));
  };

  const handleClick = (index: number) => {
    dispatch(setActiveFieldIndex(index));
    setEditDrawerIsOpen(true);
  };

  const activeField =
    activeFieldIndex != null ? fields[activeFieldIndex] : null;

  return (
    <Box>
      <Table size="sm" data-testid="dataset-fields-table">
        <Thead>
          <Tr>
            {columns.map((c) => (
              <Th key={c.name} pl={0} data-testid={`column-${c.name}`}>
                {c.name}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {fields.map((field, idx) => (
            <Tr
              key={field.name}
              _hover={{ bg: "gray.50" }}
              cursor="pointer"
              onClick={() => handleClick(idx)}
              tabIndex={0}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleClick(idx);
                }
              }}
              data-testid={`field-row-${field.name}`}
            >
              {columns.map((c) => (
                <Td key={`${c.name}-${field.name}`} pl={0}>
                  {(() => {
                    if (c.attribute === "data_qualifier") {
                      return (
                        <IdentifiabilityTag
                          dataQualifierName={field[c.attribute] ?? ""}
                        />
                      );
                    }
                    if (c.attribute === "data_categories") {
                      return field[c.attribute]?.map((dc) => (
                        <Box key={`${field.name}-${dc}`} mr={2} mb={2}>
                          <DataCategoryTag name={dc} />
                        </Box>
                      ));
                    }
                    return field[c.attribute];
                  })()}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      {activeField ? (
        <EditFieldDrawer
          isOpen={editDrawerIsOpen}
          onClose={handleClose}
          field={activeField}
        />
      ) : null}
    </Box>
  );
};

export default DatasetFieldsTable;
