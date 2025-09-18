import {
  AntForm as Form,
  AntInput as Input,
  AntModal as Modal,
  AntModalProps as ModalProps,
  AntSelect as Select,
} from "fidesui";

import {
  FIELD_TYPE_OPTIONS_NEW,
  RESOURCE_TYPE_OPTIONS,
} from "~/features/common/custom-fields/constants";
import {
  useAddCustomFieldDefinitionMutation,
  useUpdateCustomFieldDefinitionMutation,
} from "~/features/plus/plus.slice";
import {
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
} from "~/types/api";

interface CustomFieldModalV2Props extends ModalProps {
  field?: CustomFieldDefinitionWithId;
  onClose?: () => void;
}

type CustomFieldsFormValues =
  | CustomFieldDefinition
  | CustomFieldDefinitionWithId;

const CustomFieldModalV2 = ({
  field,
  onClose,
  ...props
}: CustomFieldModalV2Props) => {
  const [form] = Form.useForm<CustomFieldsFormValues>();
  const [addCustomFieldDefinition, { isLoading: addIsLoading }] =
    useAddCustomFieldDefinitionMutation();
  const [updateCustomFieldDefinition, { isLoading: updateIsLoading }] =
    useUpdateCustomFieldDefinitionMutation();

  const handleSubmit = async (values: CustomFieldsFormValues) => {
    console.log(values);
  };

  const handleCancel = () => {
    if (onClose) {
      onClose();
    }
    form.resetFields();
  };

  return (
    <Modal
      {...props}
      width="768px"
      title={field ? `Edit ${field.name}` : "Add custom field"}
      onCancel={handleCancel}
      onOk={() => handleSubmit(form.getFieldsValue())}
      confirmLoading={addIsLoading || updateIsLoading}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={field || {}}
        validateTrigger={["onBlur", "onChange"]}
      >
        <Form.Item
          label="Name"
          name="name"
          rules={[{ required: true, message: "Please enter a name" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item label="Description" name="description">
          <Input.TextArea rows={2} />
        </Form.Item>

        <Form.Item
          label="Resource Type"
          name="resource_type"
          rules={[{ required: true, message: "Please select a resource type" }]}
        >
          <Select
            options={RESOURCE_TYPE_OPTIONS}
            getPopupContainer={(trigger) =>
              trigger.parentElement || document.body
            }
          />
        </Form.Item>

        <Form.Item
          label="Field Type"
          name="field_type"
          rules={[{ required: true, message: "Please select a field type" }]}
        >
          <Select
            options={FIELD_TYPE_OPTIONS_NEW}
            getPopupContainer={(trigger) =>
              trigger.parentElement || document.body
            }
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CustomFieldModalV2;
