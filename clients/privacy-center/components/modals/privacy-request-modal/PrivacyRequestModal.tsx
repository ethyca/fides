import React, { useCallback, useState } from "react";

import { useConfig } from "~/features/common/config.slice";

import RequestModal from "../RequestModal";
import PrivacyRequestForm from "./PrivacyRequestForm";
import VerificationForm from "../VerificationForm";
import RequestSubmitted from "./RequestSubmitted";

import { ModalViews, VerificationType } from "../types";

export const usePrivacyRequestModal = () => {
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

  const successHandler = useCallback(() => {
    setCurrentView(ModalViews.RequestSubmitted);
  }, [setCurrentView]);

  return {
    isOpen,
    onClose,
    onOpen,
    openAction,
    currentView,
    setCurrentView,
    privacyRequestId,
    setPrivacyRequestId,
    successHandler,
  };
};

export type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  openAction: string | null;
  currentView: ModalViews;
  setCurrentView: (view: ModalViews) => void;
  privacyRequestId: string;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

export const PrivacyRequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  openAction,
  currentView,
  setCurrentView,
  privacyRequestId,
  setPrivacyRequestId,
  isVerificationRequired,
  successHandler,
}) => {
  const config = useConfig();
  const action = openAction
    ? config.actions.filter(({ policy_key }) => policy_key === openAction)[0]
    : null;

  if (!action) {
    return null;
  }

  let form = null;

  if (currentView === ModalViews.PrivacyRequest) {
    form = (
      <PrivacyRequestForm
        isOpen={isOpen}
        onClose={onClose}
        openAction={openAction}
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
        requestId={privacyRequestId}
        setCurrentView={setCurrentView}
        resetView={ModalViews.PrivacyRequest}
        verificationType={VerificationType.PrivacyRequest}
        successHandler={successHandler}
      />
    );
  }

  if (currentView === ModalViews.RequestSubmitted) {
    form = <RequestSubmitted onClose={onClose} />;
  }

  return (
    <RequestModal isOpen={isOpen} onClose={onClose}>
      {form}
    </RequestModal>
  );
};
