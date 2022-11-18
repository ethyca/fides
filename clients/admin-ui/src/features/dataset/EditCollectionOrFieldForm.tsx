import { Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useMemo, useState } from "react";
import { useSelector } from "react-redux";

import { selectDataCategories } from "~/features/taxonomy/taxonomy.slice";
import { DatasetCollection, DatasetField } from "~/types/api";

import { CustomSelect, CustomTextInput } from "../common/form/inputs";
import { selectClassifyInstanceField } from "../plus/plus.slice";
import { COLLECTION, DATA_QUALIFIERS, FIELD } from "./constants";
import DataCategoryInput from "./DataCategoryInput";
import { DataCategoryWithConfidence } from "./types";

export const FORM_ID = "edit-collection-or-field-form";

const IDENTIFIER_OPTIONS = DATA_QUALIFIERS.map((dq) => ({
  value: dq.key,
  label: dq.label,
}));

type FormValues =
  | Pick<DatasetField, "description" | "data_qualifier" | "data_categories">
  | Pick<
      DatasetCollection,
      "description" | "data_qualifier" | "data_categories"
    >;

interface Props {
  values: FormValues;
  onSubmit: (values: FormValues) => void;
  // NOTE: If you're adding more checks on dataType, refactor this into two
  // components instead and remove this prop.
  dataType: "collection" | "field";
}

const EditCollectionOrFieldForm = ({ values, onSubmit, dataType }: Props) => {
  const initialValues: FormValues = {
    description: values.description ?? "",
    data_qualifier: values.data_qualifier,
    data_categories: values.data_categories,
  };
  const allDataCategories = useSelector(selectDataCategories);

  // This data is only relevant for editing a field. Maybe another reason to split the field/
  // collection cases into two components.
  const classifyField = useSelector(selectClassifyInstanceField);
  const mostLikelyCategories: DataCategoryWithConfidence[] | undefined =
    useMemo(() => {
      if (!(allDataCategories && classifyField)) {
        return undefined;
      }

      const dataCategoryMap = new Map(
        allDataCategories.map((dc) => [dc.fides_key, dc])
      );
      return classifyField.classifications.map(
        ({ label, aggregated_score }) => {
          const dc = dataCategoryMap.get(label);

          return {
            fides_key: label,
            confidence: aggregated_score,
            ...dc,
          };
        }
      );
    }, [allDataCategories, classifyField]);

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    () => {
      if (initialValues.data_categories?.length) {
        return initialValues.data_categories;
      }

      // If there are classifier suggestions, choose the highest-confidence option.
      if (mostLikelyCategories?.length) {
        const topCategory = mostLikelyCategories.reduce((maxCat, nextCat) =>
          (nextCat.confidence ?? 0) > (maxCat.confidence ?? 0)
            ? nextCat
            : maxCat
        );
        return [topCategory.fides_key];
      }

      return [];
    }
  );

  const descriptionTooltip =
    dataType === "collection"
      ? COLLECTION.description.tooltip
      : FIELD.description.tooltip;
  const dataQualifierTooltip =
    dataType === "collection"
      ? COLLECTION.data_qualifiers.tooltip
      : FIELD.data_qualifier.tooltip;
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
          <CustomSelect
            name="data_qualifier"
            label="Identifiability"
            options={IDENTIFIER_OPTIONS}
            tooltip={dataQualifierTooltip}
            isSearchable={false}
            data-testid="identifiability-input"
          />
          <DataCategoryInput
            dataCategories={allDataCategories}
            mostLikelyCategories={mostLikelyCategories}
            checked={checkedDataCategories}
            onChecked={setCheckedDataCategories}
            tooltip={dataCategoryTooltip}
          />
        </Stack>
      </Form>
    </Formik>
  );
};

export default EditCollectionOrFieldForm;
