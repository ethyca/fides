import { Form, Paragraph, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { isErrorResult } from "~/types/errors";

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
  const messageApi = useMessage();
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
      }).then((result) => {
        if (isErrorResult(result)) {
          messageApi.error(getErrorMessage(result.error));
        }
      });
    }
  };

  const handleChange = (value: string) => {
    form.setFieldValue("description", value);
  };

  const handleEnd = () => {
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
                  onEnd: handleEnd,
                }
          }
        >
          {description}
        </Paragraph>
      </Form.Item>
    </Form>
  );
};
