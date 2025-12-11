"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { ReactNode, useEffect } from "react";

import { useHasConfig } from "~/features/common/config.slice";

/**
 * This is a client component that relies on having the config loaded into the providers by the homepage component.
 * If the config is not loaded, it redirect to the homepage
 */

export const ConfigGate = ({ children }: { children: ReactNode }) => {
  const hasConfig = useHasConfig();
  const router = useRouter();
  const params = useSearchParams();
  const shouldRedirect = !hasConfig && params?.get("redirect") !== "false";

  useEffect(() => {
    if (shouldRedirect) {
      router.push(`/`);
    }
  }, [shouldRedirect, router]);

  if (!hasConfig) {
    return null;
  }
  return children;
};
