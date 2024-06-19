import { CustomizableMessagingTemplatesEnum } from "~/features/messaging-templates/CustomizableMessagingTemplatesEnum";

const CustomizableMessagingTemplatesLabelEnum: Record<
  CustomizableMessagingTemplatesEnum,
  string
> = {
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_COMPLETE_ACCESS]:
    "Privacy request complete access",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_COMPLETE_DELETION]:
    "Privacy request complete deletion",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_RECEIPT]:
    "Privacy request receipt",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_REVIEW_APPROVE]:
    "Privacy request review approve",
  [CustomizableMessagingTemplatesEnum.PRIVACY_REQUEST_REVIEW_DENY]:
    "Privacy request review deny",
  [CustomizableMessagingTemplatesEnum.SUBJECT_IDENTITY_VERIFICATION]:
    "Subject identity verification",
};
export default CustomizableMessagingTemplatesLabelEnum;
