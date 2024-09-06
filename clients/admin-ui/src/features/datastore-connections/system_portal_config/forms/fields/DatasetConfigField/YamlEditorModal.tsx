// eslint-disable-next-line import/no-extraneous-dependencies
import { Box } from "fidesui";

import AddModal from "~/features/configure-consent/AddModal";
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
  <AddModal
    isOpen={isOpen}
    onClose={onClose}
    size="xl"
    returnFocusOnClose={returnFocusOnClose ?? true}
    isCentered
    title={title ?? "Edit Dataset"}
  >
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
  </AddModal>
);

export default YamlEditorModal;
