import { useState } from "react";

import { useMessage } from "fidesui";

import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth/auth.slice";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { PrivacyRequestEntity } from "../types";

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
    try {
      const headers = new Headers();
      addCommonHeaders(headers, token);

      const resp = await fetch(
        `${process.env.NEXT_PUBLIC_FIDESCTL_API}/privacy-request/${privacyRequest.id}/diagnostics`,
        { headers },
      );

      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        message.error(
          body?.detail ?? "Unable to download troubleshooting data",
        );
        return;
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `diagnostics-${privacyRequest.id}.zip`;
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      message.error("Unable to download troubleshooting data");
    } finally {
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
