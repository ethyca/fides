import { useMessage } from "fidesui";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth/auth.slice";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { PrivacyRequestEntity } from "../types";

export const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const useDownloadPrivacyRequestDiagnostics = ({
  privacyRequest,
}: {
  privacyRequest: PrivacyRequestEntity;
}) => {
  const message = useMessage();
  const token = useAppSelector(selectToken);
  const [isLoading, setIsLoading] = useState(false);

  const hasPermissionsToReadPrivacyRequests = useHasPermission([
    ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ]);

  const downloadTroubleshootingData = async () => {
    setIsLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60_000);
    try {
      const headers = new Headers();
      addCommonHeaders(headers, token);

      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_FIDESCTL_API}/privacy-request/${privacyRequest.id}/diagnostics`,
        { headers, signal: controller.signal },
      );

      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        message.error(
          body?.detail ?? "Unable to download troubleshooting data",
        );
        return;
      }

      const blob = await resp.blob();
      downloadBlob(blob, `diagnostics-${privacyRequest.id}.zip`);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        message.error("Download timed out. Please try again.");
      } else {
        message.error("Unable to download troubleshooting data");
      }
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
    }
  };

  const showDownloadTroubleshootingData = hasPermissionsToReadPrivacyRequests;

  return {
    showDownloadTroubleshootingData,
    downloadTroubleshootingData,
    isLoading,
  };
};

export default useDownloadPrivacyRequestDiagnostics;
