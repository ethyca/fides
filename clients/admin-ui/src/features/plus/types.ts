export type Page<T> = {
  items: T[];
  page: number;
  pages: number;
  size: number;
  total: number;
};

export type DictEntry = {
  id: string;
  legal_name: string;
  privacy_policy: string;
  dpo: string;
  legal_address: string;
  international_transfers: boolean;
  legal_basis_for_transfers?: string;
  uses_profiling: boolean;
  legal_basis_for_profiling?: string;
  data_security_practices?: string;
  tags?: string;
  logo?: string;
  cookies: DictCookie[];
  description: string;
};

export type CookieType = "web" | "cookie";

export type DictCookie = {
  identifier: string;
  type: CookieType;
  purposes: string;
  vendor_id: string;
  domains: string;
};
