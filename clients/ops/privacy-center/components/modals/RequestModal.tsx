<<<<<<< HEAD
import React, { useState } from "react";
import { Modal, ModalContent, ModalOverlay } from "@fidesui/react";

import type { AlertState } from "../../types/AlertState";

import config from "../../config/config.json";

import { ModalViews } from "./types";
import PrivacyRequestForm from "./PrivacyRequestForm";
import VerificationForm from "./VerificationForm";
import RequestSubmitted from "./RequestSubmitted";

export const useRequestModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [openAction, setOpenAction] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<ModalViews>(
    ModalViews.PrivacyRequest
  );
  const [privacyRequestId, setPrivacyRequestId] = useState<string>("");

  const onOpen = (action: string) => {
    setOpenAction(action);
    setIsOpen(true);
  };

  const onClose = () => {
    setIsOpen(false);
    setOpenAction(null);
    setCurrentView(ModalViews.PrivacyRequest);
    setPrivacyRequestId("");
  };

  return {
    isOpen,
    onClose,
    onOpen,
    openAction,
    currentView,
    setCurrentView,
    privacyRequestId,
    setPrivacyRequestId,
  };
};

export type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: string | null;
  setAlert: (state: AlertState) => void;
  currentView: ModalViews;
  setCurrentView: (view: ModalViews) => void;
  privacyRequestId: string;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
};

export const RequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  openAction,
  setAlert,
  currentView,
  setCurrentView,
  privacyRequestId,
  setPrivacyRequestId,
  isVerificationRequired,
}) => {
  const action = openAction
    ? config.actions.filter(({ policy_key }) => policy_key === openAction)[0]
    : null;

  if (!action) return null;

  let form = null;

  if (currentView === ModalViews.PrivacyRequest) {
    form = (
      <PrivacyRequestForm
        isOpen={isOpen}
        onClose={onClose}
        openAction={openAction}
        setAlert={setAlert}
        setCurrentView={setCurrentView}
        setPrivacyRequestId={setPrivacyRequestId}
        isVerificationRequired={isVerificationRequired}
      />
    );
  }

  if (currentView === ModalViews.IdentityVerification) {
    form = (
      <VerificationForm
        isOpen={isOpen}
        onClose={onClose}
        openAction={openAction}
        setAlert={setAlert}
        privacyRequestId={privacyRequestId}
        setCurrentView={setCurrentView}
      />
    );
  }

  if (currentView === ModalViews.RequestSubmitted) {
    form = <RequestSubmitted onClose={onClose} action={action} />;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent top={[0, "205px"]} maxWidth="464px" mx={5} my={3}>
        {form}
      </ModalContent>
    </Modal>
  );
};
=======
import React from "react";
import { Modal, ModalContent, ModalOverlay } from "@fidesui/react";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const RequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  children,
}) => (
  <Modal isOpen={isOpen} onClose={onClose}>
    <ModalOverlay />
    <ModalContent top={[0, "205px"]} maxWidth="464px" mx={5} my={3}>
      {children}
    </ModalContent>
  </Modal>
);

export default RequestModal;
>>>>>>> unified-fides-2
