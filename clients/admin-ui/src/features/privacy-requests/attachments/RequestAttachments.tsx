import {
  AntButton as Button,
  AntMessage as message,
  AntTitle as Title,
  AntTooltip as Tooltip,
  AntUpload as Upload,
  Icons,
  UploadFile,
} from "fidesui";
import { useCallback } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import FidesSpinner from "~/features/common/FidesSpinner";
import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";
import { ScopeRegistryEnum } from "~/types/api";
import { AttachmentType } from "~/types/api/models/AttachmentType";

import { useGetActiveStorageQuery } from "../privacy-requests.slice";
import {
  useGetAttachmentsQuery,
  useUploadAttachmentMutation,
} from "./privacy-request-attachments.slice";

interface RequestAttachmentsProps {
  subjectRequest: PrivacyRequestEntity;
}

const RequestAttachments = ({ subjectRequest }: RequestAttachmentsProps) => {
  const canUserReadAttachments = useHasPermission([
    ScopeRegistryEnum.ATTACHMENT_READ,
  ]);
  const canUserUploadAttachments = useHasPermission([
    ScopeRegistryEnum.ATTACHMENT_CREATE,
  ]);

  const currentUser = useAppSelector(selectUser);
  const [uploadAttachment] = useUploadAttachmentMutation();
  const {
    data: activeStorage,
    isLoading: isLoadingStorage,
    error: activeStorageError,
  } = useGetActiveStorageQuery();

  const { data: attachments, isLoading: isLoadingAttachments } =
    useGetAttachmentsQuery({
      privacy_request_id: subjectRequest.id,
      user_id: currentUser?.id || "",
    });

  const defaultFileList: UploadFile[] =
    attachments?.items.map((attachment) => {
      const isExternalLink = attachment.download_url.startsWith("http");
      return {
        uid: attachment.id,
        name: attachment.file_name,
        status: "done" as const,
        url: isExternalLink ? attachment.download_url : undefined,
      };
    }) || [];

  const renderAttachmentIcon = useCallback(() => <Icons.Attachment />, []);

  const downloadIcon = useCallback((file: UploadFile) => {
    if (file.url) {
      return <Icons.Download />;
    }
    return (
      <Tooltip title="Download is not available when using local storage methods">
        <Icons.Download />
      </Tooltip>
    );
  }, []);

  if (!canUserReadAttachments) {
    return null;
  }

  const isAddButtonEnabled = canUserUploadAttachments && activeStorage?.key;

  return (
    <div>
      <div className="mt-6">
        <div className="mb-6">
          <Title level={2}>Attachments</Title>
        </div>
        {isLoadingStorage || isLoadingAttachments ? (
          <FidesSpinner size="md" alignment="start" />
        ) : (
          <Upload
            name="attachment_file"
            defaultFileList={defaultFileList}
            iconRender={renderAttachmentIcon}
            showUploadList={{
              showRemoveIcon: false,
              showDownloadIcon: true,
              downloadIcon,
            }}
            customRequest={async (options) => {
              const { file, onSuccess, onError } = options;
              const fileName = (file as File).name;

              try {
                await uploadAttachment({
                  privacy_request_id: subjectRequest.id,
                  user_id: currentUser?.id || "",
                  attachment_file: file as File,
                  storage_key: activeStorage.key,
                  attachment_type: AttachmentType.INTERNAL_USE_ONLY,
                }).unwrap();

                message.success(`${fileName} file uploaded successfully`);
                onSuccess?.(file);
              } catch (err) {
                message.error(`${fileName} file upload failed.`);
                onError?.(err as Error);
              }
            }}
            className="[&_.ant-upload-list]:mt-4"
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
                <Button
                  icon={<Icons.Add />}
                  iconPosition="end"
                  disabled={!isAddButtonEnabled}
                >
                  Add
                </Button>
              </Tooltip>
            )}
          </Upload>
        )}
      </div>
    </div>
  );
};

export default RequestAttachments;
