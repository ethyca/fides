import { Flex, Form, Input } from "fidesui";
import { useState } from "react";
import { useSelector } from "react-redux";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import { selectDataCategories } from "~/features/taxonomy/data-category.slice";
import { DatasetCollection, DatasetField } from "~/types/api";

import { COLLECTION, FIELD } from "./constants";
import { DataCategoryInput } from "./DataCategoryInput";

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

export const EditCollectionOrFieldForm = ({
  values,
  onSubmit,
  dataType,
  showDataCategories = true,
}: Props) => {
  const [form] = Form.useForm<{ description: string }>();
  const allEnabledDataCategories = useSelector(selectDataCategories).filter(
    (category) => category.active,
  );

  const [checkedDataCategories, setCheckedDataCategories] = useState<string[]>(
    values.data_categories || [],
  );

  const descriptionTooltip =
    dataType === "collection"
      ? COLLECTION.description.tooltip
      : FIELD.description.tooltip;
  const dataCategoryTooltip =
    dataType === "collection"
      ? COLLECTION.data_categories.tooltip
      : FIELD.data_categories.tooltip;

  const handleFinish = (formValues: { description: string }) => {
    // data categories need to be handled separately since they are not a typical form element
    const newValues: FormValues = {
      ...formValues,
      data_categories: checkedDataCategories,
    };
    onSubmit(newValues);
  };

  return (
    <Form
      form={form}
      id={FORM_ID}
      layout="vertical"
      initialValues={{
        description: values.description ?? "",
      }}
      onFinish={handleFinish}
      key={values.description}
    >
      <Form.Item
        name="description"
        label={
          <Flex align="center" gap="small">
            Description
            <InfoTooltip label={descriptionTooltip} />
          </Flex>
        }
      >
        <Input data-testid="description-input" />
      </Form.Item>
      {showDataCategories && (
        <DataCategoryInput
          dataCategories={allEnabledDataCategories}
          checked={checkedDataCategories}
          onChecked={setCheckedDataCategories}
          tooltip={dataCategoryTooltip}
        />
      )}
    </Form>
  );
};
