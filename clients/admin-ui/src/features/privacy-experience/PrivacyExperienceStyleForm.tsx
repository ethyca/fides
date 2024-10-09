import { AntButton as Button, Heading } from "fidesui";

import { CustomSelect } from "~/features/common/form/inputs";
import { PrivacyExperienceConfigColumnLayout } from "~/features/privacy-experience/PrivacyExperienceForm";

const colorOptions = [
  {
    value: "cadetblue",
    label: "Cadet Blue",
  },
  {
    value: "tomato",
    label: "Tomato",
  },
  {
    value: "limegreen",
    label: "Lime Green",
  },
];

const PrivacyExperienceStyleForm = ({
  onReturnToMainForm,
}: {
  onReturnToMainForm: () => void;
}) => {
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
      <CustomSelect
        label="Heading color"
        name="color"
        options={colorOptions}
        variant="stacked"
      />
    </PrivacyExperienceConfigColumnLayout>
  );
};

export default PrivacyExperienceStyleForm;
