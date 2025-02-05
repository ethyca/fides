import {
  AntButton,
  AntFlex as Flex,
  AntTypography as Typography,
  ModalProps,
} from "fidesui";
import { useState } from "react";

import FormModal from "~/features/common/modals/FormModal";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";

const { Text } = Typography;

interface AddDataUsesModalProps extends Omit<ModalProps, "children"> {
  onSave: (dataUses: string[]) => void;
  isSaving?: boolean;
}

const AddDataUsesModal = ({
  onSave,
  isSaving,
  onClose,
  ...props
}: AddDataUsesModalProps) => {
  const [selectedDataUses, setSelectedDataUses] = useState<string[]>([]);

  const handleReset = () => {
    setSelectedDataUses([]);
    onClose();
  };

  return (
    <FormModal title="Add consent category" {...props} onClose={handleReset}>
      <Flex vertical gap={20} className="pb-6 pt-4">
        <Text>
          Assign consent categories to selected assets. This configures the
          system for consent management. Consent categories apply to both
          individual assets and the system.
        </Text>
        <ConsentCategorySelect
          mode="tags"
          selectedTaxonomies={selectedDataUses}
          onSelect={(_, option) =>
            setSelectedDataUses([...selectedDataUses, option.value])
          }
          variant="outlined"
        />
      </Flex>
      <Flex justify="space-between">
        <AntButton
          htmlType="reset"
          onClick={handleReset}
          data-testid="cancel-btn"
        >
          Cancel
        </AntButton>
        <AntButton
          htmlType="submit"
          type="primary"
          disabled={!selectedDataUses.length}
          loading={isSaving}
          onClick={() => onSave(selectedDataUses)}
          data-testid="save-btn"
        >
          Save
        </AntButton>
      </Flex>
    </FormModal>
  );
};

export default AddDataUsesModal;
