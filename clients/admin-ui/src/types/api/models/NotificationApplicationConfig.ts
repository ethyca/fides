/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API model - configuration settings for data subject and/or data processor notifications
 */
export type NotificationApplicationConfig = {
  send_request_completion_notification?: boolean;
  send_request_receipt_notification?: boolean;
  send_request_review_notification?: boolean;
  notification_service_type?: string;
};
