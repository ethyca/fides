import { headers } from "next/headers";

export async function getNonce() {
  return (await headers()).get("x-nonce");
}
