import { AntButton as Button, AntModal, Icons } from "fidesui";
import { useState } from "react";

import SharedMonitorConfigForm from "~/features/monitors/SharedMonitorConfigForm";
import SharedMonitorConfigTable from "~/features/monitors/SharedMonitorConfigTable";
import { SharedMonitorConfig } from "~/types/api";

const SharedConfigModal = () => {
  const [modalIsOpen, setModalIsOpen] = useState(false);

  const [formIsOpen, setFormIsOpen] = useState(false);

  const [configToEdit, setConfigToEdit] = useState<
    SharedMonitorConfig | undefined
  >(undefined);

  const handleRowClick = (row: SharedMonitorConfig) => {
    setConfigToEdit(row);
    setFormIsOpen(true);
    setModalIsOpen(true);
  };

  const resetForm = () => {
    setFormIsOpen(false);
    setConfigToEdit(undefined);
  };

  const handleCancel = () => {
    resetForm();
    setModalIsOpen(false);
  };

  return (
    <>
      <Button
        className="absolute right-10 top-6"
        type="primary"
        icon={<Icons.Settings />}
        iconPosition="end"
        onClick={() => setModalIsOpen(true)}
      >
        Configurations
      </Button>
      <AntModal
        open={modalIsOpen}
        onCancel={handleCancel}
        destroyOnClose
        centered
        width={768}
      >
        {formIsOpen ? (
          <SharedMonitorConfigForm
            config={configToEdit}
            onBackClick={resetForm}
          />
        ) : (
          <SharedMonitorConfigTable
            onNewClick={() => setFormIsOpen(true)}
            onRowClick={handleRowClick}
          />
        )}
      </AntModal>
    </>
  );
};

export default SharedConfigModal;
