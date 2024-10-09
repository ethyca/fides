export interface ConfigMessagingDetailsRequest {
  service_type: string;
  details?: {
    is_eu_domain?: string;
    domain?: string;
    twilio_email_from?: string;
  };
}

export interface ConfigMessagingSecretsRequest {
  service_type?: string;
  details?: {
    twilio_api_key?: string;
    mailgun_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_messaging_service_sid?: string;
    twilio_sender_phone_number?: string;
  };
}

export interface ConfigMessagingRequest {
  type: string;
}
