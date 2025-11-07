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
import { GearLightIcon } from "~/features/common/Icon";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";
import { Property } from "~/types/api";

const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
const PROPERTY_UNIQUE_ID_TEMPLATE = "{property-unique-id}";
const FIDES_JS_SCRIPT_TEMPLATE = `<script>
!(function () {
    // Recommended: Fides override settings
    window.fides_overrides = {
      fides_consent_non_applicable_flag_mode: "include",
      fides_consent_flag_type: "boolean",
    };

    // Optional: Initialize integrations like Google Tag Manager or BlueConic
    addEventListener("FidesInitialized", function () {
      // Fides.gtm();
      // Fides.blueconic();
    });

    // Recommended: wrapper script that allows for dynamic switching of geolocation by adding query params to the window URL
    // query param prefix is "fides_"
    // eg, "fides_geolocation=US-CA"
    var fidesPrefix = "fides_";
    var searchParams = new URLSearchParams(location.search);
    var fidesSearchParams = new URLSearchParams();
    searchParams.forEach(function (value, key) {
      if (key.startsWith(fidesPrefix)) {
        fidesSearchParams.set(
          key.replace(fidesPrefix, ""),
          key === fidesPrefix + "cache_bust" ? Date.now().toString() : value,
        );
      }
    });

    // Required: core Fides JS script
    var src = "https://${PRIVACY_CENTER_HOSTNAME_TEMPLATE}/fides.js?property_id=${PROPERTY_UNIQUE_ID_TEMPLATE}" + fidesSearchParams.toString();
    var script = document.createElement("script");
    script.setAttribute("src", src);
    document.head.appendChild(script);
  })();
</script>`;

interface Props {
  property: Property;
}

const NewJavaScriptTag = ({ property }: Props) => {
  const modal = useDisclosure();
  const initialRef = useRef(null);
  const { fidesCloud: isFidesCloud } = useFeatures();

  const { data: fidesCloudConfig, isSuccess } = useGetFidesCloudConfigQuery(
    undefined,
    {
      skip: !isFidesCloud,
    },
  );

  const fidesJsScriptTag = useMemo(() => {
    const script = FIDES_JS_SCRIPT_TEMPLATE.replace(
      PROPERTY_UNIQUE_ID_TEMPLATE,
      property.id!.toString(),
    );
    if (isFidesCloud && isSuccess && fidesCloudConfig?.privacy_center_url) {
      script.replace(
        PRIVACY_CENTER_HOSTNAME_TEMPLATE,
        fidesCloudConfig.privacy_center_url,
      );
    }
    return script;
  }, [fidesCloudConfig?.privacy_center_url, isFidesCloud, isSuccess, property]);

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
