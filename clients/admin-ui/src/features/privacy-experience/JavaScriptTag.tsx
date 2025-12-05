import {
  AntButton as Button,
  Code,
  FormControl,
  FormLabel,
  Input,
  Link,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from "fidesui";
import { useMemo, useRef, useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { CopyIcon } from "~/features/common/Icon";
import {
  FIDES_JS_SCRIPT_TEMPLATE,
  PRIVACY_CENTER_HOSTNAME_TEMPLATE,
} from "./fidesJsScriptTemplate";

const JavaScriptTag = () => {
  const modal = useDisclosure();
  const initialRef = useRef(null);
  const [privacyCenterHostname, setPrivacyCenterHostname] = useState("");

  const fidesJsScriptTag = useMemo(
    () => {
      let script = FIDES_JS_SCRIPT_TEMPLATE;

      // Remove the property_id query parameter for this component
      script = script.replaceAll("?property_id={property-unique-id}", "?");
      if (privacyCenterHostname) {
        script = script.replaceAll(
          PRIVACY_CENTER_HOSTNAME_TEMPLATE,
          privacyCenterHostname,
        );
      }
      return script;
    },
    [privacyCenterHostname],
  );

  return (
    <>
      <Button
        onClick={modal.onOpen}
        icon={<CopyIcon />}
        iconPosition="end"
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
                website, as high up in the &lt;head&gt; as possible. Enter your
                privacy center&apos;s hostname and path below to generate the
                complete script.
              </Text>
              <FormControl>
                <FormLabel>Privacy Center Hostname</FormLabel>
                <Input
                  value={privacyCenterHostname}
                  onChange={(e) => setPrivacyCenterHostname(e.target.value)}
                  placeholder="example.com/privacy-center"
                  data-testid="privacy-center-hostname-input"
                />
              </FormControl>
              <Code
                display="flex"
                justifyContent="space-between"
                alignItems="flex-start"
                p={0}
                position="relative"
              >
                <Text
                  p={4}
                  whiteSpace="pre"
                  fontFamily="mono"
                  fontSize="sm"
                  flex={1}
                  maxH="400px"
                  overflowX="auto"
                  overflowY="auto"
                >
                  {fidesJsScriptTag}
                </Text>
                <ClipboardButton copyText={fidesJsScriptTag} />
              </Code>
              <Text>
                For more information about adding a JavaScript tag to your
                website, please visit{" "}
                <Link
                  color="complimentary.500"
                  href="https://docs.ethyca.com/tutorials/consent-management-configuration/install-fides#install-fidesjs-script-on-your-website"
                  isExternal
                >
                  docs.ethyca.com
                </Link>
              </Text>
            </Stack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default JavaScriptTag;
