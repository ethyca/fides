// eslint-disable-next-line import/no-extraneous-dependencies
import {
  Box,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "fidesui";

import { Dataset } from "~/types/api";

import YamlEditor from "./YamlEditor";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onChange: (value: Dataset) => void;
  onSubmit?: () => void;
  title?: string;
  isLoading?: boolean;
  returnFocusOnClose?: boolean;
  isDatasetSelected: boolean;
  dataset?: Dataset;
}
const YamlEditorModal = ({
  isOpen,
  onClose,
  title,
  isLoading,
  returnFocusOnClose,
  isDatasetSelected,
  dataset,
  onChange,
  onSubmit,
}: Props) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="xl"
    returnFocusOnClose={returnFocusOnClose ?? true}
    isCentered
  >
    <ModalOverlay />
    <ModalContent textAlign="center" data-testid="YamlEditorModal">
      <ModalHeader fontWeight="medium" pb={0}>
        {title}
      </ModalHeader>
      <ModalBody>
        <Box data-testid="yaml-editor-section">
          <YamlEditor
            data={dataset ? [dataset] : []}
            onSubmit={onSubmit}
            isSubmitting={false}
            disabled={isDatasetSelected}
            onChange={onChange}
            isLoading={isLoading}
            onCancel={onClose}
          />
        </Box>
      </ModalBody>
    </ModalContent>
  </Modal>
);

export default YamlEditorModal;
