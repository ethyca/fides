import { Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useMemo, useState } from "react";
import { useSelector } from "react-redux";

import { CustomTextInput } from "~/features/common/form/inputs";
import { DataCategoryWithConfidence } from "~/features/dataset/types";
import { initialDataCategories } from "~/features/plus/helpers";
import { selectClassifyInstanceField } from "~/features/plus/plus.slice";
import { selectDataCategories } from "~/features/taxonomy/taxonomy.slice";
import { DatasetCollection, DatasetField } from "~/types/api";

import { COLLECTION, FIELD } from "./constants";
import DataCategoryInput from "./DataCategoryInput";

export const FORM_ID = "edit-collection-or-field-form";

type FormValues =
  | Pick<DatasetField, "description" | "data_categories">
  | Pick<DatasetCollection, "description" | "data_categories">;

interface Props {
  values: FormValues;
  onSubmit: (values: FormValues) => void;
  // NOTE: If you're adding more checks on dataType, refactor this into two
  // components instead and remove this prop.
  dataType: "collection" | "field";
  showDataCategories?: boolean;
}

const EditCollectionOrFieldForm = ({
  values,
  onSubmit,
  dataType,
  showDataCategories = true,
}: Props) => {
  const initialValues: FormValues = {
    description: values.description ?? "",
    data_categories: values.data_categories,
  };
  const allEnabledDataCategories = useSelector(selectDataCategories).filter(
    (category) => category.active,
  );

  // This data is only relevant for editing a field. Maybe another reason to split the field/
  // collection cases into two components.
  const classifyField = useSelector(selectClassifyInstanceField);
  const mostLikelyCategories: DataCategoryWithConfidence[] | undefined =
    useMemo(() => {
      if (!(allEnabledDataCategories && classifyField)) {
        return undefined;
      }

      const dataCategoryMap = new Map(
        allEnabledDataCategories.map((dc) => [dc.fides_key, dc]),
      );
      return (
        classifyField.classifications?.map(({ label, score }) => {
          const dc = dataCategoryMap.get(label);

          return {
            fides_key: label,
            confidence: score,
            ...dc,
          };
        }) ?? []
      );
    }, [allEnabledDataCategories, classifyField]);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    () =>
      initialDataCategories({
        dataCategories: initialValues.data_categories,
        mostLikelyCategories,
      }),
  );

  const descriptionTooltip =
    dataType === "collection"
      ? COLLECTION.description.tooltip
      : FIELD.description.tooltip;
  const dataCategoryTooltip =
    dataType === "collection"
      ? COLLECTION.data_categories.tooltip
      : FIELD.data_categories.tooltip;

  const handleSubmit = (formValues: FormValues) => {
    // data categories need to be handled separately since they are not a typical form element
    const newValues = {
      ...formValues,
      ...{ data_categories: checkedDataCategories },
    };
    onSubmit(newValues);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      <Form id={FORM_ID}>
        <Stack>
          <CustomTextInput
            name="description"
            label="Description"
            tooltip={descriptionTooltip}
            data-testid="description-input"
          />
          {showDataCategories && (
            <DataCategoryInput
              dataCategories={allEnabledDataCategories}
              mostLikelyCategories={mostLikelyCategories}
              checked={checkedDataCategories}
              onChecked={setCheckedDataCategories}
              tooltip={dataCategoryTooltip}
            />
          )}
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
