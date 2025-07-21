import {
  AntButton as Button,
  AntFlex as Flex,
  AntMessage as message,
  AntTitle as Title,
  AntTooltip as Tooltip,
  AntUpload as Upload,
  Icons,
  UploadFile,
} from "fidesui";
import { useCallback, useState } from "react";

import FidesSpinner from "~/features/common/FidesSpinner";
import { getErrorMessage } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { useHasPermission } from "~/features/common/Restrict";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { ScopeRegistryEnum } from "~/types/api";
import { AttachmentType } from "~/types/api/models/AttachmentType";

import { useGetActiveStorageQuery } from "../privacy-requests.slice";
import { renderUploadItem } from "./CustomUploadItem";
import {
  useGetAttachmentsQuery,
  useUploadAttachmentMutation,
} from "./privacy-request-attachments.slice";

interface RequestAttachmentsProps {
  subjectRequest: PrivacyRequestEntity;
}

interface CustomAttachmentData {
  attachment_id: string;
  privacy_request_id: string;
}

const RequestAttachments = ({ subjectRequest }: RequestAttachmentsProps) => {
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const canUserReadAttachments = useHasPermission([
    ScopeRegistryEnum.ATTACHMENT_READ,
  ]);
  const canUserUploadAttachments = useHasPermission([
    ScopeRegistryEnum.ATTACHMENT_CREATE,
  ]);

  const [uploadAttachment] = useUploadAttachmentMutation();
  const {
    data: activeStorage,
    isLoading: isLoadingStorage,
    error: activeStorageError,
  } = useGetActiveStorageQuery();

  const { data: attachments, isLoading: isLoadingAttachments } =
    useGetAttachmentsQuery({
      privacy_request_id: subjectRequest.id,
    });

  const { refetch: refetchAttachments } = useGetAttachmentsQuery({
    privacy_request_id: subjectRequest.id,
  });

  const fileList: Array<UploadFile & { customData?: CustomAttachmentData }> =
    attachments?.items.map((attachment) => {
      return {
        uid: attachment.id,
        name: attachment.file_name,
        status: "done" as const,
        customData: {
          attachment_id: attachment.id,
          privacy_request_id: subjectRequest.id,
          attachment_type: attachment.attachment_type,
        },
      };
    }) || [];

  const renderAttachmentIcon = useCallback(() => <Icons.Attachment />, []);

  if (!canUserReadAttachments) {
    return null;
  }

  const isAddButtonEnabled = canUserUploadAttachments && activeStorage?.key;

  const allowedFileExtensions = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".csv",
    ".jpg",
    ".jpeg",
    ".png",
    ".zip",
  ];
  return (
    <div>
      <div className="mt-6">
        <div className="mb-6">
          <Title level={3}>Attachments</Title>
        </div>
        {isLoadingStorage || isLoadingAttachments ? (
          <FidesSpinner size="md" alignment="start" />
        ) : (
          <Upload
            name="attachment_file"
            fileList={fileList}
            iconRender={renderAttachmentIcon}
            showUploadList={{
              showRemoveIcon: false,
              showDownloadIcon: false,
            }}
            itemRender={renderUploadItem}
            accept={allowedFileExtensions.join(",")}
            customRequest={async (options) => {
              const { file, onSuccess, onError } = options;
              const fileName = (file as File).name;

              try {
                setIsUploadingFile(true);
                await uploadAttachment({
                  privacy_request_id: subjectRequest.id,
                  attachment_file: file as File,
                  attachment_type: AttachmentType.INTERNAL_USE_ONLY,
                }).unwrap();

                message.success(`${fileName} file uploaded successfully`);

                refetchAttachments();

                onSuccess?.(file);
              } catch (err) {
                message.error(`${fileName} file upload failed.`);
                onError?.(err as Error);
              } finally {
                setIsUploadingFile(false);
              }
            }}
            disabled={!isAddButtonEnabled}
          >
            {canUserUploadAttachments && (
              <Tooltip
                title={
                  activeStorageError &&
                  `Add attachment not available: ${getErrorMessage(
                    activeStorageError,
                  )}`
                }
                placement="top"
              >
                <Flex align="center" gap={12} className="mb-4">
                  <Button
                    icon={<Icons.Add />}
                    iconPosition="end"
                    disabled={!isAddButtonEnabled || isUploadingFile}
                    loading={isUploadingFile}
                  >
                    {isUploadingFile ? "Uploading" : "Add"}
                  </Button>
                  <InfoTooltip
                    label={`Uploaded attachments are for internal use and won't be send as part of the request package.
                      Accepted filetypes: ${allowedFileExtensions.join(", ")}`}
                    placement="top"
                  />
                </Flex>
              </Tooltip>
            )}
          </Upload>
        )}
      </div>
    </div>
  );
};

export default RequestAttachments;
