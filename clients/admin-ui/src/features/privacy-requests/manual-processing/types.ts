import { PatchUploadManualWebhookDataRequest } from "~/features/privacy-requests/types";

export type ManualInputData = {
  checked: boolean;
  connection_key: string;
  fields: ManualInputDataFieldMap;
  privacy_request_id: string;
};

export type ManualInputDataFieldMap = {
  [key: string]: any;
};

export type SaveCompleteResponse = {
  connection_key: string;
  fields: ManualInputDataFieldMap;
};

export type ManualProcessingDetailProps = {
  connectorName: string;
  data: ManualInputData;
  isSubmitting: boolean;
  onSaveClick: (params: PatchUploadManualWebhookDataRequest) => void;
};
