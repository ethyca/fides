import { AntButton as Button, AntForm, AntSelect, Heading } from "fidesui";
import { useFormikContext } from "formik";

import { PrivacyExperienceConfigColumnLayout } from "~/features/privacy-experience/PrivacyExperienceForm";
import { ExperienceConfigCreate } from "~/types/api";

const elementOptions = [
  {
    label: "Text",
    value: "no-preview-notice-text",
  },
  {
    label: "Heading",
    value: "no-preview-notice-heading",
  },
];

const colorOptions = [
  {
    label: "Cadet Blue",
    value: "cadetblue",
  },
  {
    label: "Tomato",
    value: "tomato",
  },
  {
    label: "Lime Green",
    value: "limegreen",
  },
];

const sizeOptions = [
  {
    label: "Small",
    value: "12px",
  },
  {
    label: "Medium",
    value: "16px",
  },
  {
    label: "Large",
    value: "20px",
  },
];

const PrivacyExperienceStyleForm = ({
  onReturnToMainForm,
}: {
  onReturnToMainForm: () => void;
}) => {
  const [form] = AntForm.useForm();

  const { setFieldValue } = useFormikContext<
    ExperienceConfigCreate & { css: string }
  >();

  const handleValuesChanged = (_: any, all: any) => {
    if (all.element) {
      setFieldValue(
        "css",
        `#${all.element} { 
          color: ${all.color ?? "auto"}; 
          font-size: ${all.size ?? "auto"}; 
        }`,
      );
    } else {
      setFieldValue("css", "");
    }
  };

  const buttonPanel = (
    <div className="flex justify-between border-t border-[#DEE5EE] p-4">
      <Button onClick={onReturnToMainForm}>Cancel</Button>
      <Button type="primary">Save</Button>
    </div>
  );

  return (
    <PrivacyExperienceConfigColumnLayout buttonPanel={buttonPanel} pt="4">
      <Heading fontSize="md" fontWeight="semibold">
        Edit appearance
      </Heading>
      <AntForm
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChanged}
      >
        <AntForm.Item name="element" label="Element">
          <AntSelect placeholder="Choose element" options={elementOptions} />
        </AntForm.Item>
        <AntForm.Item name="color" label="Color">
          <AntSelect
            placeholder="Choose color"
            options={colorOptions}
            allowClear
          />
        </AntForm.Item>
        <AntForm.Item name="size" label="Font size">
          <AntSelect
            placeholder="Choose size"
            options={sizeOptions}
            allowClear
          />
        </AntForm.Item>
      </AntForm>
    </PrivacyExperienceConfigColumnLayout>
  );
};

export default PrivacyExperienceStyleForm;
