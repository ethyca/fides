/* eslint-disable react/no-unstable-nested-components */
import { Modal } from "fidesui";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { PreferencesSaved } from "~/types/api";

import TcfConsentTable from "./TcfConsentTable";

interface ConsentTcfDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  tcfPreferences?: PreferencesSaved;
}

const ConsentTcfDetailModal = ({
  isOpen,
  onClose,
  tcfPreferences,
}: ConsentTcfDetailModalProps) => {
  return (
    <Modal
      data-testid="consent-tcf-detail-modal"
      open={isOpen}
      onCancel={onClose}
      width={MODAL_SIZE.xl}
      centered
      destroyOnClose
      title="TCF Consent Details"
      footer={null}
    >
      <div className="mb-4">
        <TcfConsentTable tcfPreferences={tcfPreferences} />
      </div>
    </Modal>
  );
};
export default ConsentTcfDetailModal;
