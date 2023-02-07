import {
  Button,
  ButtonGroup,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  UseDisclosureReturn,
  useToast,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import React from "react";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import { User } from "./types";
import { useDeleteUserMutation } from "./user-management.slice";

const initialValues = { username: "", usernameConfirmation: "" };

const useDeleteUserModal = ({
  id,
  username,
  onClose,
}: Pick<User, "id" | "username"> & { onClose: () => void }) => {
  const toast = useToast();
  const [deleteUser] = useDeleteUserMutation();

  const handleDeleteUser = async () => {
    const result = await deleteUser(id);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully deleted user"));
      onClose();
    }
  };

  const validationSchema = Yup.object().shape({
    username: Yup.string()
      .required()
      .oneOf([username], "Username must match this user's")
      .label("Username"),
    usernameConfirmation: Yup.string()
      .required()
      .oneOf([Yup.ref("username")], "Usernames must match")
      .label("Username confirmation"),
  });

  return {
    handleDeleteUser,
    validationSchema,
  };
};

const DeleteUserModal = ({
  user,
  ...modal
}: { user: User } & UseDisclosureReturn) => {
  const { isOpen, onClose } = modal;
  const { handleDeleteUser, validationSchema } = useDeleteUserModal({
    id: user.id,
    username: user.username,
    onClose,
  });

  return (
    <Modal isCentered isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <Formik
          initialValues={initialValues}
          validationSchema={validationSchema}
          onSubmit={handleDeleteUser}
        >
          {({ isSubmitting, dirty, isValid }) => (
            <Form>
              <ModalHeader>Delete User</ModalHeader>
              <ModalCloseButton />
              <ModalBody>
                <Stack direction="column" spacing={4}>
                  <CustomTextInput name="username" label="Enter username" />
                  <CustomTextInput
                    name="usernameConfirmation"
                    label="Confirm username"
                  />
                </Stack>
              </ModalBody>

              <ModalFooter>
                <ButtonGroup size="sm" spacing="2" width="100%">
                  <Button onClick={onClose} variant="outline" width="50%">
                    Cancel
                  </Button>
                  <Button
                    colorScheme="primary"
                    disabled={!dirty || !isValid}
                    isLoading={isSubmitting}
                    type="submit"
                    width="50%"
                    data-testid="submit-btn"
                  >
                    Delete User
                  </Button>
                </ButtonGroup>
              </ModalFooter>
            </Form>
          )}
        </Formik>
      </ModalContent>
    </Modal>
  );
};

export default DeleteUserModal;
