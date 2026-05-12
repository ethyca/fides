import { Form, Input } from "fidesui";
import snakeCase from "lodash.snakecase";
import { useEffect } from "react";

const NoticeKeyField = ({ isEditing }: { isEditing: boolean }) => {
  const form = Form.useFormInstance();
  const name = Form.useWatch("name", form);

  useEffect(() => {
    if (!isEditing && name !== undefined && name !== null) {
      form.setFieldsValue({ notice_key: snakeCase(name) });
    }
  }, [name, isEditing, form]);

  return (
    <Form.Item name="notice_key" label="Key used in Fides cookie">
      <Input data-testid="input-notice_key" />
    </Form.Item>
  );
};

export { NoticeKeyField };
