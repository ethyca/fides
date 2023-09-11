import { Button, useDisclosure } from "@fidesui/react";

import AddModal from "./AddModal";

const AddCookie = () => {
  const modal = useDisclosure();
  const handleSuggestions = () => {
    /* TODO */
  };
  return (
    <>
      <Button onClick={modal.onOpen}>Add cookie</Button>
      <AddModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        title="Add a cookie"
        onSuggestionClick={handleSuggestions}
      >
        TODO
      </AddModal>
    </>
  );
};

export default AddCookie;
