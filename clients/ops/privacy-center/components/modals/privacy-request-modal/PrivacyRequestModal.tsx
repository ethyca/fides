import React, { useCallback, useState } from "react";
import RequestModal from "../RequestModal";

import type { AlertState } from "../../../types/AlertState";

import config from "../../../config/config.json";

import PrivacyRequestForm from "./PrivacyRequestForm";
import VerificationForm from "../VerificationForm";
import RequestSubmitted from "./RequestSubmitted";

import { ModalViews, VerificationType } from "../types";

export const usePrivactRequestModal = () => {
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
  setAlert: (state: AlertState) => void;
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
  setAlert,
  currentView,
  setCurrentView,
  privacyRequestId,
  setPrivacyRequestId,
  isVerificationRequired,
  successHandler,
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
        setAlert={setAlert}
        requestId={privacyRequestId}
        setCurrentView={setCurrentView}
        resetView={ModalViews.PrivacyRequest}
        verificationType={VerificationType.PrivacyRequest}
        successHandler={successHandler}
      />
    );
  }

  if (currentView === ModalViews.RequestSubmitted) {
    form = <RequestSubmitted onClose={onClose} action={action} />;
  }

  return (
    <RequestModal isOpen={isOpen} onClose={onClose}>
      {form}
    </RequestModal>
  );
};
