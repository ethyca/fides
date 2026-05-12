import { Flex, Form, Input } from "fidesui";

import { Dataset } from "~/types/api";

import { InfoTooltip } from "../common/InfoTooltip";
import { DATASET } from "./constants";

export const FORM_ID = "edit-dataset-form";

type FormValues = Pick<Dataset, "name" | "description">;

interface Props {
  values: Partial<Dataset>;
  onSubmit: (values: Partial<Dataset>) => void;
}

export const EditDatasetForm = ({ values, onSubmit }: Props) => {
  const [form] = Form.useForm<FormValues>();

  const handleFinish = (formValues: FormValues) => {
    const newValues = {
      ...formValues,
      data_categories: values.data_categories || [],
    };
    onSubmit(newValues);
  };

  return (
    <Form
      form={form}
      id={FORM_ID}
      layout="vertical"
      initialValues={{
        name: values.name ?? "",
        description: values.description ?? "",
      }}
      onFinish={handleFinish}
      key={values.fides_key}
    >
      <Form.Item
        name="name"
        label={
          <Flex align="center" gap="small">
            Name
            <InfoTooltip label={DATASET.name.tooltip} />
          </Flex>
        }
      >
        <Input data-testid="input-name" />
      </Form.Item>
      <Form.Item
        name="description"
        label={
          <Flex align="center" gap="small">
            Description
            <InfoTooltip label={DATASET.description.tooltip} />
          </Flex>
        }
      >
        <Input data-testid="input-description" />
      </Form.Item>
    </Form>
  );
};
