export interface ConfigMessagingDetailsRequest {
  service_type: string;
  details?: {
    is_eu_domain?: string;
    domain?: string;
    twilio_email_from?: string;
  };
  secrets?: {
    mailgun_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_messaging_service_sid?: string;
    twilio_sender_phone_number?: string;
    api_key?: string;
  };
}

export interface MessageDetails {
  details: {
    api_version: string;
    domain: string;
    is_eu_domain: boolean;
  };
  key: string;
  name: string;
  service_type: string;
}

export interface ConfigMessagingRequest {
  type: string;
}
