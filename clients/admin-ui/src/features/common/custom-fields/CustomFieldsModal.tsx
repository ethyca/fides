import {
  Box,
  Button,
  ButtonGroup,
  Divider,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  useDisclosure,
} from "@fidesui/react";
import * as React from "react";
import { useRef, useState } from "react";

import ConfirmationModal from "~/features/common/ConfirmationModal";
import DataTabs from "~/features/common/DataTabs";
import { ResourceTypes } from "~/types/api";

import { ChooseFromLibrary } from "./ChooseFromLibrary";
import { TabTypes } from "./constants";
import { CreateCustomFields } from "./CreateCustomFields";
import { CreateCustomLists } from "./CreateCustomLists";
import { CustomFieldsButton } from "./CustomFieldsButton";
import { Tab } from "./types";

type CustomFieldsModalProps = {
  resourceType: ResourceTypes;
};

const CustomFieldsModal: React.FC<CustomFieldsModalProps> = ({
  resourceType,
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const btnRef = useRef(null);
  const createCustomFieldsRef = useRef(null);
  const createCustomListsRef = useRef(null);
  const chooseFromLibraryRef = useRef(null);
  const firstField = useRef(null);

  const DEFAULT_TAB_INDEX = TabTypes.CREATE_CUSTOM_FIELDS;
  const [tabIndex, setTabIndex] = useState(DEFAULT_TAB_INDEX);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirmationModalOpen, setConfirmationModalOpen] = useState(false);

  const getActiveFormRef = () => {
    let formRef: any;
    switch (tabIndex) {
      case TabTypes.CREATE_CUSTOM_FIELDS:
        formRef = createCustomFieldsRef!.current as any;
        break;
      case TabTypes.CREATE_CUSTOM_LISTS:
        formRef = createCustomListsRef!.current as any;
        break;
      case TabTypes.CHOOSE_FROM_LIBRARY:
        formRef = chooseFromLibraryRef!.current as any;
        break;
      default:
        break;
    }
    return formRef;
  };

  const handleClose = (force?: boolean) => {
    const activeForm = getActiveFormRef();
    if (!force && activeForm?.getDirty()) {
      setConfirmationModalOpen(true);
      return;
    }
    setTabIndex(DEFAULT_TAB_INDEX);
    setIsSubmitting(false);
    onClose();
  };

  const handleSaveClick = () => {
    const activeForm = getActiveFormRef();
    if (activeForm) {
      activeForm.submitForm();
      setIsSubmitting(activeForm.isSubmitting);
    }
  };

  const handleSubmitComplete = () => {
    setIsSubmitting(false);
  };

  const handleTabsChange = (index: number) => setTabIndex(index);

  const tabList: Tab[] = [
    {
      label: "Create custom fields",
      content: (
        <CreateCustomFields
          onSubmitComplete={handleSubmitComplete}
          ref={createCustomFieldsRef}
          resourceType={resourceType}
        />
      ),
      submitButtonText: "Save",
    },
    {
      label: "Create custom lists",
      content: (
        <CreateCustomLists
          onSubmitComplete={handleSubmitComplete}
          ref={createCustomListsRef}
        />
      ),
      submitButtonText: "Save to library",
    },
    {
      label: "Choose from library",
      content: (
        <ChooseFromLibrary
          onSubmitComplete={handleSubmitComplete}
          ref={chooseFromLibraryRef}
          resourceType={resourceType}
        />
      ),
      submitButtonText: "Save",
    },
  ];

  return (
    <>
      <Flex mb="20px">
        <CustomFieldsButton btnRef={btnRef} onClick={onOpen} />
      </Flex>
      <Modal
        finalFocusRef={btnRef}
        initialFocusRef={firstField}
        isCentered
        isOpen={isOpen}
        motionPreset="slideInBottom"
        onClose={handleClose}
      >
        <ModalOverlay />
        <ModalContent maxW="680px">
          <ModalHeader>
            <Text
              color="black"
              fontSize="lg"
              fontWeight="medium"
              lineHeight="36px"
            >
              Add custom field
            </Text>
            <Divider color="gray.200" mt="8px" />
            <Box mt="16px">
              <Text
                color="gray.600"
                fontSize="sm"
                fontWeight="light"
                lineHeight="20px"
              >
                Fill in the information below to add a new custom field to this
                form or view the library to select from existing custom fields.
              </Text>
            </Box>
          </ModalHeader>
          <ModalCloseButton size="sm" />
          <ModalBody>
            <DataTabs
              data={tabList}
              defaultIndex={DEFAULT_TAB_INDEX}
              fontSize="sm"
              flexGrow={1}
              onChange={handleTabsChange}
            />
          </ModalBody>
          <ModalFooter justifyContent="flex-start" padding="0px 24px 24px 24px">
            <ButtonGroup size="sm" spacing="8px" variant="outline">
              <Button
                onClick={() => {
                  handleClose();
                }}
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                _active={{ bg: "primary.500" }}
                _disabled={{ opacity: "inherit" }}
                _hover={{ bg: "primary.400" }}
                bg="primary.800"
                color="white"
                data-testid="custom-fields-modal-submit-btn"
                isDisabled={isSubmitting}
                isLoading={isSubmitting}
                loadingText="Submitting"
                onClick={handleSaveClick}
                size="sm"
                type="button"
                variant="solid"
              >
                {tabList[tabIndex].submitButtonText}
              </Button>
            </ButtonGroup>
          </ModalFooter>
        </ModalContent>

        <ConfirmationModal
          cancelButtonText="Continue editing"
          continueButtonText="Discard"
          isCentered
          isOpen={isConfirmationModalOpen}
          onClose={() => {
            setConfirmationModalOpen(false);
          }}
          onConfirm={() => {
            setConfirmationModalOpen(false);
            handleClose(true);
          }}
          title="Unsaved changes"
          message={
            <Text color="gray.500">
              You have unsaved changes, are you sure you want to discard?
            </Text>
          }
        />
      </Modal>
    </>
  );
};

export { CustomFieldsModal };
