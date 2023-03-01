import { Box, Tooltip } from "@fidesui/react";

import { getTopClassification } from "~/features/dataset/helpers";
import IdentifiabilityTag from "~/features/taxonomy/IdentifiabilityTag";
import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
import { ClassifyField, DatasetField } from "~/types/api";

// This component is used within a Chakra Td element in the DatasetFieldsTable. Chakra requires a
// JSX.Element in that context, so all returns in this component need to be wrapped in a fragment.
/* eslint-disable react/jsx-no-useless-fragment */
const DatasetFieldCell = ({
  attribute,
  field,
  classifyField,
}: {
  attribute: keyof DatasetField;
  field: DatasetField;
  classifyField?: ClassifyField;
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
    const topClassification =
      classifyField !== undefined
        ? getTopClassification(classifyField)
        : undefined;

    const classifiedCategory =
      topClassification !== undefined ? [topClassification.label] : [];

    const assignedCategories = field.data_categories ?? [];
    // Only show the classified categories if none have been directly assigned to the dataset.
    const categories =
      assignedCategories.length > 0 ? assignedCategories : classifiedCategory;

    return (
      <Tooltip
        placement="right"
        label={
          // TODO: Related to #724, the design wants this to be clickable but our tooltip doesn't support that.
          categories === classifiedCategory
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

export default DatasetFieldCell;
