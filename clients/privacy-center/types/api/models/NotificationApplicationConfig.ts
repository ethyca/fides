/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API model - configuration settings for data subject and/or data processor notifications
 */
export type NotificationApplicationConfig = {
  send_request_completion_notification?: boolean | null;
  send_request_receipt_notification?: boolean | null;
  send_request_review_notification?: boolean | null;
  notification_service_type?: string | null;
  enable_property_specific_messaging?: boolean | null;
};
