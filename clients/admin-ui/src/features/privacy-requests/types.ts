import {string} from "prop-types";

export type PrivacyRequestStatus =
  | 'approved'
  | 'complete'
  | 'denied'
  | 'error'
  | 'in_processing'
  | 'paused'
  | 'pending';


export interface DenyPrivacyRequest{
  id:string,
  reason: string
}

export interface PrivacyRequest {
  status: PrivacyRequestStatus;
  identity: {
    email?: string;
    phone?: string;
  };
  policy: {
    name: string;
    key: string;
  };
  reviewer: {
    id: string;
    username: string;
  };
  created_at: string;
  reviewed_by: string;
  id: string;
}

export interface PrivacyRequestResponse {
  items: PrivacyRequest[];
  total: number;
}

export interface PrivacyRequestParams {
  status?: PrivacyRequestStatus;
  id: string;
  from: string;
  to: string;
  page: number;
  size: number;
}
