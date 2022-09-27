import { Box, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { selectClassifyInstanceFieldMap } from "~/features/common/plus.slice";

<<<<<<< HEAD:clients/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
import IdentifiabilityTag from "../taxonomy/IdentifiabilityTag";
import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
=======
>>>>>>> unified-fides-2:clients/ctl/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
import {
  selectActiveEditor,
  selectActiveField,
  selectActiveFields,
  setActiveEditor,
  setActiveFieldIndex,
} from "./dataset.slice";
<<<<<<< HEAD:clients/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
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
=======
import DatasetFieldCell from "./DatasetFieldCell";
import EditFieldDrawer from "./EditFieldDrawer";
import { ColumnMetadata, EditableType } from "./types";
>>>>>>> unified-fides-2:clients/ctl/admin-ui/src/features/dataset/DatasetFieldsTable.tsx

interface Props {
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ columns }: Props) => {
  const dispatch = useDispatch();
  const activeFields = useSelector(selectActiveFields);
  const activeField = useSelector(selectActiveField);
  const activeEditor = useSelector(selectActiveEditor);
<<<<<<< HEAD:clients/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
=======
  const classifyInstanceFieldMap = useSelector(selectClassifyInstanceFieldMap);
>>>>>>> unified-fides-2:clients/ctl/admin-ui/src/features/dataset/DatasetFieldsTable.tsx

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
<<<<<<< HEAD:clients/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
                  <Cell field={field} attribute={c.attribute} />
=======
                  <DatasetFieldCell
                    field={field}
                    classifyField={classifyInstanceFieldMap.get(field.name)}
                    attribute={c.attribute}
                  />
>>>>>>> unified-fides-2:clients/ctl/admin-ui/src/features/dataset/DatasetFieldsTable.tsx
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
