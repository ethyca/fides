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
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import { useForceResetUserPasswordMutation } from "./user-management.slice";

const ValidationSchema = Yup.object().shape({
  password: passwordValidation.label("Password"),
  passwordConfirmation: Yup.string()
    .required()
    .oneOf([Yup.ref("password")], "Passwords must match")
    .label("Password confirmation"),
});
const initialValues = { password: "", passwordConfirmation: "" };
type FormValues = typeof initialValues;

const useNewPasswordModal = (id: string) => {
  const modal = useDisclosure();
  const toast = useToast();
  const [resetPassword] = useForceResetUserPasswordMutation();

  const handleResetPassword = async (values: FormValues) => {
    const result = await resetPassword({
      id,
      new_password: values.password,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          "Successfully reset user's password. Please inform the user of their new password.",
        ),
      );
      modal.onClose();
    }
  };

  return {
    ...modal,
    handleResetPassword,
  };
};

interface Props {
  id: string;
}

const NewPasswordModal = ({ id }: Props) => {
  const { handleResetPassword, isOpen, onClose, onOpen } =
    useNewPasswordModal(id);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={onOpen}
        data-testid="reset-password-btn"
      >
        Reset password
      </Button>
      <Modal isCentered isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <Formik
            initialValues={initialValues}
            validationSchema={ValidationSchema}
            onSubmit={handleResetPassword}
          >
            {({ isSubmitting, dirty, isValid }) => (
              <Form>
                <ModalHeader>Reset Password</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                  <Stack direction="column" spacing={4}>
                    <Text mb={2}>Choose a new password for this user.</Text>
                    <CustomTextInput
                      name="password"
                      label="Password"
                      placeholder="********"
                      type="password"
                      tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                    />
                    <CustomTextInput
                      name="passwordConfirmation"
                      label="Confirm Password"
                      placeholder="********"
                      type="password"
                      tooltip="Must match above password."
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
                      isDisabled={!dirty || !isValid}
                      isLoading={isSubmitting}
                      type="submit"
                      width="50%"
                      data-testid="submit-btn"
                    >
                      Change Password
                    </Button>
                  </ButtonGroup>
                </ModalFooter>
              </Form>
            )}
          </Formik>
        </ModalContent>
      </Modal>
    </>
  );
};

export default NewPasswordModal;
