import {
  Alert,
  AlertDescription,
  AlertIcon,
  AntButton as Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  UseDisclosureReturn,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import React from "react";
import * as Yup from "yup";

import { useAppDispatch } from "~/app/hooks";
import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import { User } from "./types";
import {
  setActiveUserId,
  useDeleteUserMutation,
} from "./user-management.slice";

const initialValues = { username: "", usernameConfirmation: "" };

const useDeleteUserModal = ({
  id,
  username,
  onClose,
}: Pick<User, "id" | "username"> & { onClose: () => void }) => {
  const toast = useToast();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [deleteUser] = useDeleteUserMutation();

  const handleDeleteUser = async () => {
    const result = await deleteUser(id);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully deleted user"));
      onClose();
    }
    dispatch(setActiveUserId(undefined));
    router.push(USER_MANAGEMENT_ROUTE);
  };

  const validationSchema = Yup.object().shape({
    usernameConfirmation: Yup.string()
      .required()
      .oneOf([username], "Confirmation input must match the username")
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
      <ModalContent data-testid="delete-user-modal">
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
                <Alert status="warning" overflow="visible">
                  <AlertIcon />
                  <AlertDescription>
                    <Text as="span" mb={2}>
                      You are about to delete the user&nbsp;
                    </Text>
                    <Text
                      as="span"
                      mb={2}
                      fontStyle="italic"
                      fontWeight="semibold"
                    >
                      {user.username}.
                    </Text>
                    <Text mb={2}>
                      This action cannot be undone. To confirm, please enter the
                      user&rsquo;s username below.
                    </Text>
                  </AlertDescription>
                </Alert>

                <Stack direction="column" spacing={4}>
                  <CustomTextInput
                    name="usernameConfirmation"
                    label="Confirm username"
                    placeholder="Type the username to delete"
                  />
                </Stack>
              </ModalBody>

              <ModalFooter>
                <div className="w-full gap-2">
                  <Button onClick={onClose} className="w-1/2">
                    Cancel
                  </Button>
                  <Button
                    type="primary"
                    disabled={!dirty || !isValid}
                    loading={isSubmitting}
                    htmlType="submit"
                    className="w-1/2"
                    data-testid="submit-btn"
                  >
                    Delete User
                  </Button>
                </div>
              </ModalFooter>
            </Form>
          )}
        </Formik>
      </ModalContent>
    </Modal>
  );
};

export default DeleteUserModal;
