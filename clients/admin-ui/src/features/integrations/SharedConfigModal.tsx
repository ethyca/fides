import { Button, Form, Icons } from "fidesui";
import { useState } from "react";

import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import SharedMonitorConfigForm from "~/features/monitors/SharedMonitorConfigForm";
import SharedMonitorConfigTable from "~/features/monitors/SharedMonitorConfigTable";
import { SharedMonitorConfig } from "~/types/api";

enum SharedConfigModalState {
  MAIN_VIEW = "main",
  FORM_VIEW = "form",
}

const SharedConfigModal = () => {
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [form] = Form.useForm();

  const [configToEdit, setConfigToEdit] = useState<
    SharedMonitorConfig | undefined
  >(undefined);

  const [modalState, setModalState] = useState<SharedConfigModalState>(
    SharedConfigModalState.MAIN_VIEW,
  );

  const handleRowClick = (row: SharedMonitorConfig) => {
    setConfigToEdit(row);
    setModalState(SharedConfigModalState.FORM_VIEW);
    setModalIsOpen(true);
  };

  const resetForm = () => {
    form.resetFields();
    setModalState(SharedConfigModalState.MAIN_VIEW);
    setConfigToEdit(undefined);
  };

  const handleCancel = () => {
    form.resetFields();
    resetForm();
    setModalIsOpen(false);
  };

  return (
    <>
      <Button
        icon={<Icons.Settings />}
        iconPlacement="end"
        onClick={() => setModalIsOpen(true)}
        data-testid="configurations-btn"
      >
        Shared configs
      </Button>
      <ConfirmCloseModal
        open={modalIsOpen}
        onClose={handleCancel}
        getIsDirty={() =>
          modalState === SharedConfigModalState.FORM_VIEW &&
          form.isFieldsTouched()
        }
        destroyOnHidden
        centered
        width={MODAL_SIZE.lg}
        footer={null}
      >
        {modalState === SharedConfigModalState.FORM_VIEW && (
          <SharedMonitorConfigForm
            config={configToEdit}
            onBackClick={resetForm}
            form={form}
          />
        )}
        {modalState === SharedConfigModalState.MAIN_VIEW && (
          <SharedMonitorConfigTable
            onNewClick={() => setModalState(SharedConfigModalState.FORM_VIEW)}
            onRowClick={handleRowClick}
          />
        )}
      </ConfirmCloseModal>
    </>
  );
};

export default SharedConfigModal;
