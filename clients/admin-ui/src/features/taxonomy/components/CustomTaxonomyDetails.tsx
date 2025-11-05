import {
  AntDescriptions as Descriptions,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
} from "fidesui";

import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

interface CustomTaxonomyDetailsProps {
  taxonomy?: TaxonomyResponse;
  onSubmit: (values: TaxonomyUpdate) => void;
  formId: string;
}

const CustomTaxonomyDetails = ({
  taxonomy,
  onSubmit,
  formId,
}: CustomTaxonomyDetailsProps) => {
  if (!taxonomy) {
    return null;
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { fides_key, ...initialValues } = taxonomy;

  return (
    <Flex vertical gap="large">
      <Descriptions>
        <Descriptions.Item label="Fides key">{fides_key}</Descriptions.Item>
      </Descriptions>
      <Form
        id={formId}
        layout="vertical"
        initialValues={initialValues}
        onFinish={onSubmit}
      >
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Name is required" }]}
        >
          <Input />
        </Form.Item>
        <Form.Item label="Description" name="description">
          <Input.TextArea />
        </Form.Item>
      </Form>
    </Flex>
  );
};

export default CustomTaxonomyDetails;
