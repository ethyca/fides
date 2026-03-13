import {
  Button,
  ChakraCheckbox as Checkbox,
  ChakraSimpleGrid as SimpleGrid,
  Modal,
} from "fidesui";
import { useState } from "react";

import { usePicker } from "~/features/common/hooks/usePicker";
import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { LocationRegulationBase } from "~/types/api";

import { HeaderCheckboxRow } from "./modal";

const RegulationModal = ({
  regulations,
  isOpen,
  onClose,
  selected,
  onChange,
}: {
  regulations: LocationRegulationBase[];
  isOpen: boolean;
  onClose: () => void;
  selected: Array<string>;
  onChange: (newSelected: Array<string>) => void;
}) => {
  const [draftSelected, setDraftSelected] = useState(selected);

  const { allSelected, handleToggleAll, handleToggleSelection } = usePicker({
    items: regulations,
    selected: draftSelected,
    onChange: setDraftSelected,
  });
  const numSelected = draftSelected.length;

  const handleApply = () => {
    onChange(draftSelected);
    onClose();
  };

  const continentName = regulations[0].continent;

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnClose
      width={MODAL_SIZE.md}
      data-testid="regulation-modal"
      title="Select regulations"
      footer={
        <div className="flex w-full justify-between">
          <Button onClick={onClose} data-testid="cancel-btn">
            Cancel
          </Button>
          <Button type="primary" onClick={handleApply} data-testid="apply-btn">
            Apply
          </Button>
        </div>
      }
    >
      <HeaderCheckboxRow
        title={continentName as string}
        allSelected={allSelected}
        onToggleAll={handleToggleAll}
        numSelected={numSelected}
      />
      <SimpleGrid columns={3} spacing={6} paddingInline={4}>
        {regulations.map((regulation) => (
          <Checkbox
            size="sm"
            colorScheme="complimentary"
            key={regulation.id}
            isChecked={draftSelected.includes(regulation.id)}
            onChange={() => handleToggleSelection(regulation.id)}
            data-testid={`${regulation.name}-checkbox`}
          >
            {regulation.name}
          </Checkbox>
        ))}
      </SimpleGrid>
    </Modal>
  );
};

export default RegulationModal;
