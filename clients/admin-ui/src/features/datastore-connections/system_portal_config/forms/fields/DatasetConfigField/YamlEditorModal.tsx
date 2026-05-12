import { Modal } from "fidesui";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { Dataset } from "~/types/api";

import YamlEditor from "./YamlEditor";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onChange: (value: Dataset) => void;
  onSubmit?: () => void;
  title?: string;
  isLoading?: boolean;
  isDatasetSelected: boolean;
  dataset?: Dataset;
}
const YamlEditorModal = ({
  isOpen,
  onClose,
  title,
  isLoading,
  isDatasetSelected,
  dataset,
  onChange,
  onSubmit,
}: Props) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    centered
    destroyOnHidden
    width={MODAL_SIZE.lg}
    title={title ?? "Edit Dataset"}
    footer={null}
  >
    <div data-testid="yaml-editor-section">
      <YamlEditor
        data={dataset ? [dataset] : []}
        onSubmit={onSubmit}
        isSubmitting={false}
        disabled={isDatasetSelected}
        onChange={onChange}
        isLoading={isLoading}
        onCancel={onClose}
      />
    </div>
  </Modal>
);

export default YamlEditorModal;
