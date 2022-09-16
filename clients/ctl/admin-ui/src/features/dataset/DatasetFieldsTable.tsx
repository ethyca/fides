import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { DatasetField } from "~/types/api";

import IdentifiabilityTag from "../taxonomy/IdentifiabilityTag";
import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import {
  selectActiveEditor,
  selectActiveFieldIndex,
  setActiveEditor,
  setActiveFieldIndex,
} from "./dataset.slice";
import EditFieldDrawer from "./EditFieldDrawer";
import { ColumnMetadata, EditableType } from "./types";

interface Props {
  fields: DatasetField[];
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ fields, columns }: Props) => {
  const dispatch = useDispatch();
  const activeFieldIndex = useSelector(selectActiveFieldIndex);
  const activeEditor = useSelector(selectActiveEditor);

  const handleClose = () => {
    dispatch(setActiveFieldIndex(undefined));
    dispatch(setActiveEditor(undefined));
  };

  const handleClick = (index: number) => {
    dispatch(setActiveFieldIndex(index));
    dispatch(setActiveEditor(EditableType.FIELD));
  };

  const activeField =
    activeFieldIndex !== undefined ? fields[activeFieldIndex] : undefined;

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
                          <TaxonomyEntityTag name={dc} />
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
          isOpen={activeEditor === EditableType.FIELD}
          onClose={handleClose}
          field={activeField}
        />
      ) : null}
    </Box>
  );
};

export default DatasetFieldsTable;
