import { Box, Table, Tbody, Td, Th, Thead, Tooltip, Tr } from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { selectClassifyInstanceFieldMap } from "~/features/common/plus.slice";
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
  classifyInstanceField,
}: {
  attribute: keyof DatasetField;
  field: DatasetField;
  classifyInstanceField?: DatasetField;
}): JSX.Element => {
  if (attribute === "data_qualifier") {
    const dataQualifierName = field.data_qualifier;

    return (
      <>
        {dataQualifierName ? (
          <IdentifiabilityTag dataQualifierName={dataQualifierName} />
        ) : null}
      </>
    );
  }

  if (attribute === "data_categories") {
    const classifiedCategories = classifyInstanceField?.data_categories ?? [];
    const assignedCategories = field.data_categories ?? [];
    // Only show the classified categories if none have been directly assigned to the dataset.
    const categories =
      assignedCategories.length > 0 ? assignedCategories : classifiedCategories;

    return (
      <Tooltip
        placement="right"
        label={
          // TODO: Related to #724, the design wants this to be clickable but our tooltip doesn't support that.
          categories === classifiedCategories
            ? "Fides has generated these data categories for you. You can override them by modifying the field."
            : ""
        }
      >
        <Box display="inline-block">
          {categories.map((dc) => (
            <Box key={`${field.name}-${dc}`} mr={2} mb={2}>
              <TaxonomyEntityTag name={dc} />
            </Box>
          ))}
        </Box>
      </Tooltip>
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
  const classifyInstanceFieldMap = useSelector(selectClassifyInstanceFieldMap);

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
                  <Cell
                    field={field}
                    classifyInstanceField={classifyInstanceFieldMap.get(
                      field.name
                    )}
                    attribute={c.attribute}
                  />
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
