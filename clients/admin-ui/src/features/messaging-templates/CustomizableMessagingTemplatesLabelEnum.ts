import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";

const CustomizableMessagingTemplatesLabelEnum: Record<
  CustomizableMessagingTemplatesEnum,
  string
> = {
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_COMPLETE_ACCESS]:
    "Access request completed",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_COMPLETE_DELETION]:
    "Erasure request completed",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_RECEIPT]:
    "Privacy request received",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_REVIEW_APPROVE]:
    "Privacy request approved",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_REVIEW_DENY]:
    "Privacy request denied",
  [CustomizableMessagingTemplatesEnum.SUBJECT_IDENTITY_VERIFICATION]:
    "Subject identity verification",
};
export default CustomizableMessagingTemplatesLabelEnum;
