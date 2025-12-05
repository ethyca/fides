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
import { useFeatures } from "~/features/common/features";
import { GearLightIcon } from "~/features/common/Icon";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";
import { Property } from "~/types/api";
import {
  FIDES_JS_SCRIPT_TEMPLATE,
  PRIVACY_CENTER_HOSTNAME_TEMPLATE,
  PROPERTY_UNIQUE_ID_TEMPLATE,
} from "./fidesJsScriptTemplate";

interface Props {
  property: Property;
}

const NewJavaScriptTag = ({ property }: Props) => {
  const modal = useDisclosure();
  const initialRef = useRef(null);
  const [privacyCenterHostname, setPrivacyCenterHostname] = useState("");
  const { fidesCloud: isFidesCloud } = useFeatures();

  const { data: fidesCloudConfig, isSuccess } = useGetFidesCloudConfigQuery(
    undefined,
    {
      skip: !isFidesCloud,
    },
  );

  const fidesJsScriptTag = useMemo(() => {
    let script = FIDES_JS_SCRIPT_TEMPLATE.replaceAll(
      PROPERTY_UNIQUE_ID_TEMPLATE,
      property.id!.toString(),
    );
    // Use user input if provided, otherwise fall back to Fides Cloud config
    const hostname =
      privacyCenterHostname ||
      (isFidesCloud && isSuccess && fidesCloudConfig?.privacy_center_url
        ? fidesCloudConfig.privacy_center_url
        : "");
    if (hostname) {
      script = script.replaceAll(PRIVACY_CENTER_HOSTNAME_TEMPLATE, hostname);
    }
    return script;
  }, [
    fidesCloudConfig?.privacy_center_url,
    isFidesCloud,
    isSuccess,
    property,
    privacyCenterHostname,
  ]);

  return (
    <>
      <Button
        aria-label="Install property"
        size="small"
        className="mr-[10px]"
        icon={<GearLightIcon />}
        onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
          e.stopPropagation();
          modal.onOpen();
        }}
      />
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
            Install Fides Consent Manager
          </ModalHeader>
          <ModalBody pt={3} pb={6} fontSize="14px" fontWeight={500}>
            <Stack spacing={3}>
              <Text>
                Copy the code below and paste it onto every page of the{" "}
                {property.name} property.
              </Text>
              <Text>
                Paste this code as high in the <b>&lt;head&gt;</b> of the
                page as possible:
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

export default NewJavaScriptTag;
