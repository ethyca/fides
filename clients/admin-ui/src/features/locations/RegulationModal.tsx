import {
  Checkbox,
  Modal,
  ModalBody,
  ModalContent,
  ModalOverlay,
  SimpleGrid,
} from "fidesui";
import { useState } from "react";

import { usePicker } from "~/features/common/hooks/usePicker";
import { LocationRegulationBase } from "~/types/api";

import { Footer, Header, HeaderCheckboxRow } from "./modal";

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
    <Modal size="2xl" isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent data-testid="regulation-modal">
        <Header title="Select regulations" />
        <ModalBody p={6} maxHeight="70vh" overflowY="auto">
          <HeaderCheckboxRow
            title={continentName}
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
        </ModalBody>
        <Footer onApply={handleApply} onClose={onClose} />
      </ModalContent>
    </Modal>
  );
};

export default RegulationModal;
