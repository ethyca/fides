import { Select } from "fidesui";
import { FormInstance } from "antd";

interface TemplateVariable {
  name: string;
  description: string;
  example_value?: string;
}

interface TemplateVariableInsertProps {
  variables: TemplateVariable[];
  targetField: string;
  form: FormInstance;
  loading?: boolean;
}

const TemplateVariableInsert = ({
  variables,
  targetField,
  form,
  loading,
}: TemplateVariableInsertProps) => {
  const handleInsert = (variableName: string) => {
    const current: string = form.getFieldValue(targetField) ?? "";
    const insertion = `{{ ${variableName} }}`;
    form.setFieldValue(targetField, current + insertion);
  };

  return (
    <Select
      placeholder="Insert variable..."
      loading={loading}
      value={undefined}
      style={{ width: 220, marginBottom: 16 }}
      onSelect={handleInsert}
      options={variables.map((v) => ({
        value: v.name,
        label: `${v.name}${v.description ? ` — ${v.description}` : ""}`,
      }))}
    />
  );
};

export default TemplateVariableInsert;
