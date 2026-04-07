import { Form, Paragraph } from "fidesui";

import { useUpdateInfrastructureSystemDescriptionMutation } from "../../discovery-detection.slice";

type DescriptionForm = {
  description?: string;
};

export const SystemDescriptionForm = ({
  initialValues,
  monitorId,
  stagedResourceUrn,
}: {
  initialValues: { description: string };
  monitorId: string;
  stagedResourceUrn: string;
}) => {
  const [form] = Form.useForm<DescriptionForm>();
  const description = Form.useWatch("description", form);

  const [updateDescription, { isLoading }] =
    useUpdateInfrastructureSystemDescriptionMutation();

  const handleSubmit = (values: DescriptionForm) => {
    if (values.description) {
      updateDescription({
        monitorId,
        urn: stagedResourceUrn,
        description: values.description,
      });
    }
  };

  const handleChange = (value: string) => {
    form.setFieldValue("description", value);
    form.submit();
  };

  return (
    <Form
      initialValues={initialValues}
      form={form}
      size="small"
      className="w-full"
      onFinish={handleSubmit}
      layout="vertical"
    >
      <Form.Item name="description" className="m-0" rootClassName="w-full">
        <Paragraph
          editable={
            isLoading
              ? false
              : {
                  onChange: handleChange,
                }
          }
          ellipsis={{
            rows: 3,
            expandable: "collapsible",
          }}
        >
          {description}
        </Paragraph>
      </Form.Item>
    </Form>
  );
};
