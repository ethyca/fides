import {
  AntButton as Button,
  Code,
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
import { useMemo, useRef } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { useFeatures } from "~/features/common/features";
import { CopyIcon } from "~/features/common/Icon";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";

const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
const FIDES_JS_SCRIPT_TEMPLATE = `<script src="https://${PRIVACY_CENTER_HOSTNAME_TEMPLATE}/fides.js"></script>`;
const FIDES_GTM_SCRIPT_TAG = "<script>Fides.gtm()</script>";

const JavaScriptTag = () => {
  const modal = useDisclosure();
  const initialRef = useRef(null);
  const { fidesCloud: isFidesCloud } = useFeatures();

  const { data: fidesCloudConfig, isSuccess } = useGetFidesCloudConfigQuery(
    undefined,
    {
      skip: !isFidesCloud,
    },
  );

  const fidesJsScriptTag = useMemo(
    () =>
      isFidesCloud && isSuccess && fidesCloudConfig?.privacy_center_url
        ? FIDES_JS_SCRIPT_TEMPLATE.replace(
            PRIVACY_CENTER_HOSTNAME_TEMPLATE,
            fidesCloudConfig.privacy_center_url,
          )
        : FIDES_JS_SCRIPT_TEMPLATE,
    [fidesCloudConfig?.privacy_center_url, isFidesCloud, isSuccess],
  );

  return (
    <>
      <Button
        onClick={modal.onOpen}
        size="small"
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
                website, as high up in the &lt;head&gt; as possible. Replace the
                bracketed component with your privacy center&apos;s hostname and
                path.
              </Text>
              <Code
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                p={0}
              >
                <Text p={4}>{fidesJsScriptTag}</Text>
                <ClipboardButton copyText={fidesJsScriptTag} />
              </Code>
              <Text>
                Optionally, you can enable Google Tag Manager for managing tags
                on your website by including the script tag below along with the
                Fides.js tag. Place it below the Fides.js script tag.
              </Text>
              <Code
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                p={0}
              >
                <Text p={4}>{FIDES_GTM_SCRIPT_TAG}</Text>
                <ClipboardButton copyText={FIDES_GTM_SCRIPT_TAG} />
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
