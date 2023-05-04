import { NextApiRequest } from 'next';

export interface Address {
  id?: number;
  street: string;
  city: string;
  state: string;
  zip: string;
}

export interface Customer {
  id?: number;
  address_id: number;
  email: string;
  name: string;
}

export interface UserData {
  name: string;
  street: string;
  city: string;
  state: string;
  zip: string;
  email: string;
}

export interface Product {
  id: number;
  url: string;
  name: string;
  description: string;
  price: string;
}

export interface JsonApiRequest<T> extends NextApiRequest {
  body: T;
}