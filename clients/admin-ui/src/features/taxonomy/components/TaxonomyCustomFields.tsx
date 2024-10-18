import { Formik } from "formik";

import { CustomFieldsList } from "~/features/common/custom-fields";
import { ResourceTypes } from "~/types/api";

interface TaxonomyCustomFieldsProps {
  fidesKey: string;
  taxonomyType: string;
}

const TaxonomyCustomFields = ({
  fidesKey,
  taxonomyType,
}: TaxonomyCustomFieldsProps) => {
  return (
    <Formik initialValues={{}} onSubmit={() => {}} enableReinitialize>
      <CustomFieldsList
        resourceType={ResourceTypes.DATA_CATEGORY}
        resourceFidesKey={fidesKey}
      />
    </Formik>
  );
};
export default TaxonomyCustomFields;
