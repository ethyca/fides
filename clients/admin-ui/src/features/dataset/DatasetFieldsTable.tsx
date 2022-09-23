import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { DatasetField } from "~/types/api";

import IdentifiabilityTag from "../taxonomy/IdentifiabilityTag";
import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import {
  selectActiveEditor,
  selectActiveField,
  selectActiveFields,
  setActiveEditor,
  setActiveFieldIndex,
} from "./dataset.slice";
import EditFieldDrawer from "./EditFieldDrawer";
import { ColumnMetadata, EditableType } from "./types";

// Chakra wants a JSX.Element, so all returns need to be wrapped in a fragment.
/* eslint-disable react/jsx-no-useless-fragment */
const Cell = ({
  attribute,
  field,
}: {
  attribute: keyof DatasetField;
  field: DatasetField;
}): JSX.Element => {
  if (attribute === "data_qualifier") {
    const dataQualifierName = field[attribute];
    return (
      <>
        {dataQualifierName ? (
          <IdentifiabilityTag dataQualifierName={dataQualifierName} />
        ) : null}
      </>
    );
  }

  if (attribute === "data_categories") {
    return (
      <>
        {(field[attribute] ?? []).map((dc) => (
          <Box key={`${field.name}-${dc}`} mr={2} mb={2}>
            <TaxonomyEntityTag name={dc} />
          </Box>
        ))}
      </>
    );
  }

  return <>{field[attribute]}</>;
};
/* eslint-disable react/jsx-no-useless-fragment */

interface Props {
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ columns }: Props) => {
  const dispatch = useDispatch();
  const activeFields = useSelector(selectActiveFields);
  const activeField = useSelector(selectActiveField);
  const activeEditor = useSelector(selectActiveEditor);

  const handleClose = () => {
    dispatch(setActiveFieldIndex(undefined));
    dispatch(setActiveEditor(undefined));
  };

  const handleClick = (index: number) => {
    dispatch(setActiveFieldIndex(index));
    dispatch(setActiveEditor(EditableType.FIELD));
  };

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
          {(activeFields ?? []).map((field, idx) => (
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
                  <Cell field={field} attribute={c.attribute} />
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
