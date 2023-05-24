// eslint-disable-next-line import/no-extraneous-dependencies
import { ThemingProps } from "@chakra-ui/system";
import {
  Button,
  Center,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "@fidesui/react";
import { ReactNode } from "react";
import YamlEditor from "./YamlEditor";
interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: ReactNode;
  isLoading?: boolean;
  returnFocusOnClose?: boolean;
}
const YamlEditorModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  isLoading,
  returnFocusOnClose,
}: Props) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="lg"
    returnFocusOnClose={returnFocusOnClose ?? true}
    isCentered
  >
    <ModalOverlay />
    <ModalContent textAlign="center" p={6} data-testid="YamlEditorModal">
      <ModalHeader fontWeight="medium" pb={0}>
        {title}
      </ModalHeader>
      <ModalBody></ModalBody>
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button
            variant="outline"
            mr={3}
            onClick={onClose}
            data-testid="cancel-btn"
            isDisabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            colorScheme="primary"
            onClick={onConfirm}
            data-testid="continue-btn"
            isLoading={isLoading}
          >
            Continue
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default YamlEditorModal;
