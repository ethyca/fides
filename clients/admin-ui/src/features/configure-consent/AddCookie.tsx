import { Box, Button, useDisclosure } from "@fidesui/react";

import AddModal from "./AddModal";

const AddCookie = () => {
  const modal = useDisclosure();
  const handleSuggestions = () => {
    /* TODO */
  };
  return (
    <>
      <Button onClick={modal.onOpen} data-testid="add-cookie-btn">
        Add cookie
      </Button>
      <AddModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        title="Add a cookie"
        onSuggestionClick={handleSuggestions}
      >
        <Box data-testid="add-cookie-modal-content">TODO</Box>
      </AddModal>
    </>
  );
};

export default AddCookie;
