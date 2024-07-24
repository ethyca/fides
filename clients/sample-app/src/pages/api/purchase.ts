import type { NextApiResponse } from "next";

import pool from "../../lib/db";
import { Address, Customer, JsonApiRequest, UserData } from "../../types";

interface ResponseData {
  address: Address;
  customer: Customer;
}

export default async function handler(
  req: JsonApiRequest<UserData>,
  res: NextApiResponse<ResponseData>,
) {
  const { street, city, state, zip, email, name } = req.body;

  // First, insert the new address record
  const addressResult = await pool.query<Address>(
    "INSERT INTO public.address (street, city, state, zip) VALUES ($1, $2, $3, $4) RETURNING *;",
    [street, city, state, zip],
  );
  const address = { ...addressResult.rows[0] };

  // Next, insert the new customer record
  const customerResult = await pool.query<Customer>(
    "INSERT INTO public.customer (email, name, address_id) VALUES ($1, $2, $3) RETURNING *;",
    [email, name, address.id],
  );
  const customer = { ...customerResult.rows[0] };

  res.status(200).json({ address, customer });
}
