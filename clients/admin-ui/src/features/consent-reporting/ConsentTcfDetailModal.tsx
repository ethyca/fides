/* eslint-disable react/no-unstable-nested-components */
import {
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalCloseButton as ModalCloseButton,
  ChakraModalContent as ModalContent,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
} from "fidesui";

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
      id="consent-lookup-modal"
      isOpen={isOpen}
      onClose={onClose}
      size="4xl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent data-testid="consent-tcf-detail-modal">
        <ModalCloseButton />
        <ModalHeader pb={2}>TCF Consent Details</ModalHeader>
        <ModalBody>
          <div className="mb-4">
            <TcfConsentTable tcfPreferences={tcfPreferences} />
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentTcfDetailModal;
