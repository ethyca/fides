import {
  Button,
  Code,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useRef } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { CopyIcon } from "~/features/common/Icon";

const SCRIPT_TAG =
  '<script src="https://{privacy-center-hostname-and-path}/fides.js"></script>';

const JavaScriptTag = () => {
  const modal = useDisclosure();
  const initialRef = useRef(null);

  return (
    <>
      <Button
        onClick={modal.onOpen}
        variant="outline"
        size="sm"
        rightIcon={<CopyIcon />}
        data-testid="js-tag-btn"
      >
        Get JavaScript tag
      </Button>
      <Modal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        isCentered
        size="xl"
        initialFocusRef={initialRef}
      >
        <ModalOverlay />
        <ModalContent data-testid="copy-js-tag-modal">
          {/* Setting tabIndex and a ref makes this the initial modal focus.
              This is helpful because otherwise the copy button receives the focus 
              which triggers unexpected tooltip behavior */}
          <ModalHeader tabIndex={-1} ref={initialRef} pb={0}>
            Copy JavaScript tag
          </ModalHeader>
          <ModalBody pt={3} pb={6}>
            <Stack spacing={3}>
              <Text>
                Copy the code below and paste it onto every page of your
                website, as high up in the &lt;head&gt; as possible. Replace the
                bracketed component with your privacy center&apos;s hostname and
                path.
              </Text>
              <Code display="flex" p={0}>
                <Text p={4}>{SCRIPT_TAG}</Text>
                <ClipboardButton copyText={SCRIPT_TAG} />
              </Code>
              <Text>
                For more information about adding a JavaScript tag to your
                website, visit our docs.
              </Text>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default JavaScriptTag;
