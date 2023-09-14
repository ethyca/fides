import { Box, Button, useDisclosure } from "@fidesui/react";

import AddModal from "./AddModal";

const AddVendor = () => {
  const modal = useDisclosure();
  const handleSuggestions = () => {
    /* TODO */
  };
  return (
    <>
      <Button onClick={modal.onOpen} data-testid="add-vendor-btn">
        Add vendor
      </Button>
      <AddModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        title="Add a vendor"
        onSuggestionClick={handleSuggestions}
      >
        <Box data-testid="add-vendor-modal-content">TODO</Box>
      </AddModal>
    </>
  );
};

export default AddVendor;
