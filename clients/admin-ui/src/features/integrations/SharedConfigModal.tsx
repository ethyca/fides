import { AntButton as Button, AntModal as Modal, Icons } from "fidesui";
import { useState } from "react";

import SharedMonitorConfigForm from "~/features/monitors/SharedMonitorConfigForm";
import SharedMonitorConfigTable from "~/features/monitors/SharedMonitorConfigTable";
import { SharedMonitorConfig } from "~/types/api";

enum SharedConfigModalState {
  MAIN_VIEW = "main",
  FORM_VIEW = "form",
}

const SharedConfigModal = () => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

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
    setModalState(SharedConfigModalState.MAIN_VIEW);
    setConfigToEdit(undefined);
  };

  const handleCancel = () => {
    resetForm();
    setModalIsOpen(false);
  };

  return (
    <>
      <Button
        type="primary"
        icon={<Icons.Settings />}
        iconPosition="end"
        onClick={() => setModalIsOpen(true)}
        data-testid="configurations-btn"
      >
        Shared configs
      </Button>
      <Modal
        open={modalIsOpen}
        onCancel={handleCancel}
        destroyOnClose
        centered
        width={768}
        footer={null}
      >
        {modalState === SharedConfigModalState.FORM_VIEW && (
          <SharedMonitorConfigForm
            config={configToEdit}
            onBackClick={resetForm}
          />
        )}
        {modalState === SharedConfigModalState.MAIN_VIEW && (
          <SharedMonitorConfigTable
            onNewClick={() => setModalState(SharedConfigModalState.FORM_VIEW)}
            onRowClick={handleRowClick}
          />
        )}
      </Modal>
    </>
  );
};

export default SharedConfigModal;
