import { Button, useDisclosure } from "@fidesui/react";

import AddModal from "./AddModal";

const AddVendor = () => {
  const modal = useDisclosure();
  const handleSuggestions = () => {
    /* TODO */
  };
  return (
    <>
      <Button onClick={modal.onOpen}>Add vendor</Button>
      <AddModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        title="Add a vendor"
        onSuggestionClick={handleSuggestions}
      >
        TODO
      </AddModal>
    </>
  );
};

export default AddVendor;
