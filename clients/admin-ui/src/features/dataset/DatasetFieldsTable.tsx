import { Box, Table, Tbody, Td, Th, Thead, Tr } from "fidesui";
import { useDispatch, useSelector } from "react-redux";

import { ColumnMetadata } from "~/features/common/ColumnDropdown";
import { selectClassifyInstanceFieldMap } from "~/features/plus/plus.slice";
import { DatasetField } from "~/types/api";

import {
  selectActiveEditor,
  selectActiveField,
  selectActiveFields,
  setActiveEditor,
  setActiveFieldIndex,
} from "./dataset.slice";
import DatasetFieldCell from "./DatasetFieldCell";
import EditFieldDrawer from "./EditFieldDrawer";
import { EditableType } from "./types";

interface Props {
  columns: ColumnMetadata<DatasetField>[];
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
              _hover={{ bg: "neutral.50" }}
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
                  <DatasetFieldCell
                    field={field}
                    classifyField={classifyInstanceFieldMap.get(field.name)}
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
