import {
  Button,
  ChakraCode as Code,
  ChakraLink as Link,
  ChakraStack as Stack,
  ChakraText as Text,
  Modal,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import { useMemo } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { useFeatures } from "~/features/common/features";
import { GearLightIcon } from "~/features/common/Icon";
import { useGetFidesCloudConfigQuery } from "~/features/plus/plus.slice";
import { Property } from "~/types/api";

const PRIVACY_CENTER_HOSTNAME_TEMPLATE = "{privacy-center-hostname-and-path}";
const PROPERTY_UNIQUE_ID_TEMPLATE = "{property-unique-id}";
const FIDES_JS_SCRIPT_TEMPLATE = `<script src="https://${PRIVACY_CENTER_HOSTNAME_TEMPLATE}/fides.js?property_id=${PROPERTY_UNIQUE_ID_TEMPLATE}"></script>`;
const FIDES_GTM_SCRIPT_TAG = "<script>Fides.gtm()</script>";

interface Props {
  property: Property;
}

const NewJavaScriptTag = ({ property }: Props) => {
  const modal = useDisclosure();
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
        icon={<GearLightIcon />}
        onClick={(e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
          e.stopPropagation();
          modal.onOpen();
        }}
      />
      <Modal
        open={modal.isOpen}
        onCancel={modal.onClose}
        centered
        destroyOnHidden
        data-testid="copy-js-tag-modal"
        title="Install Fides Consent Manager"
        footer={null}
      >
        {/* Setting tabIndex and a ref makes this the initial modal focus.
            This is helpful because otherwise the copy button receives the focus
            which triggers unexpected tooltip behavior */}
        <Stack spacing={3}>
          <Text>
            Copy the code below and paste it onto every page of the{" "}
            {property.name} property.
          </Text>
          <Text>
            1. Paste this code as high in the <b>&lt;head&gt;</b> of the page as
            possible:
          </Text>
          <Code
            display="flex"
            justifyContent="space-between"
            alignItems="top"
            p={0}
          >
            <Text p={4}>{fidesJsScriptTag}</Text>
            <ClipboardButton copyText={fidesJsScriptTag} />
          </Code>
          <Text>
            2. Optionally, you can enable Google Tag Manager for managing tags
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
            For more information about adding a JavaScript tag to your website,
            please visit{" "}
            <Link
              color="complimentary.500"
              href="https://docs.ethyca.com/tutorials/consent-management-configuration/install-fides#install-fidesjs-script-on-your-website"
              isExternal
            >
              docs.ethyca.com
            </Link>
          </Text>
        </Stack>
      </Modal>
    </>
  );
};

export default NewJavaScriptTag;
