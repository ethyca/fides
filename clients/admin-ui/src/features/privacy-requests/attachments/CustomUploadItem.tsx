import {
  AntButton as Button,
  AntFlex as Flex,
  AntMessage as message,
  AntText as Text,
  Icons,
  UploadFile,
} from "fidesui";
import React, { useState } from "react";

import { useLazyGetAttachmentDetailsQuery } from "./privacy-request-attachments.slice";

interface CustomAttachmentData {
  attachment_id: string;
  privacy_request_id: string;
}

interface CustomUploadItemProps {
  file: UploadFile & { customData?: CustomAttachmentData };
}

const CustomUploadItem = ({ file }: CustomUploadItemProps) => {
  const [isLoadingUrl, setIsLoadingUrl] = useState(false);

  // Use the lazy version of the query which returns a trigger function
  const [getAttachmentDetails] = useLazyGetAttachmentDetailsQuery();

  const handleDownload = async () => {
    if (file.customData?.attachment_id && file.customData?.privacy_request_id) {
      setIsLoadingUrl(true);
      try {
        const result = await getAttachmentDetails({
          privacy_request_id: file.customData.privacy_request_id,
          attachment_id: file.customData.attachment_id,
        });

        const url = result.data?.retrieved_attachment_url;
        const isExternalLink = url?.startsWith("http");

        if (url && isExternalLink) {
          window.open(url, "_blank");
        } else if (url && !isExternalLink) {
          message.info(
            `Download is not available when using local storage methods.`,
          );
        } else {
          message.error(`No download URL available for ${file.name}`);
        }
      } catch (error) {
        message.error(`Failed to fetch attachment download URL`);
      } finally {
        setIsLoadingUrl(false);
      }
    }
  };

  return (
    <Flex align="center" gap={8}>
      <Icons.Attachment className="shrink-0" />
      <Text ellipsis={{ tooltip: file.name }} className="grow">
        {file.name}
      </Text>
      <Button
        type="text"
        icon={<Icons.Download />}
        onClick={handleDownload}
        loading={isLoadingUrl}
        className="shrink-0"
      />
    </Flex>
  );
};

export default CustomUploadItem;

// Helper function for use with Upload's itemRender prop
export const renderUploadItem = (
  originNode: React.ReactElement,
  file: UploadFile & { customData?: CustomAttachmentData },
) => {
  return <CustomUploadItem file={file} />;
};
