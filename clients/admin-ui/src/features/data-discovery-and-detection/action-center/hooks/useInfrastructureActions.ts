import { useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { DiffStatus } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import {
  useMuteIdentityProviderMonitorResultMutation,
  usePromoteIdentityProviderMonitorResultMutation,
  useUnmuteIdentityProviderMonitorResultMutation,
} from "../../discovery-detection.slice";

export const useInfrastructureActions = ({
  urn,
  monitorId,
  onSuccess,
  systemName,
  diffStatus,
}: {
  urn?: string;
  monitorId: string;
  onSuccess?: () => void;
  systemName?: string;
  diffStatus?: DiffStatus;
}) => {
  const [
    promoteIdentityProviderMonitorResultMutation,
    { isLoading: isPromoting },
  ] = usePromoteIdentityProviderMonitorResultMutation();

  const [muteIdentityProviderMonitorResultMutation, { isLoading: isMuting }] =
    useMuteIdentityProviderMonitorResultMutation();

  const [
    unmuteIdentityProviderMonitorResultMutation,
    { isLoading: isUnmuting },
  ] = useUnmuteIdentityProviderMonitorResultMutation();

  const messageApi = useMessage();

  const handleApprove = async () => {
    if (!urn) {
      messageApi.error("Cannot promote: system URN is missing");
      return;
    }

    const result = await promoteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `${systemName || "System"} has been promoted to the system inventory.`,
      );
      if (onSuccess) {
        onSuccess();
      }
    }
  };

  const handleIgnore = async () => {
    if (!urn) {
      messageApi.error("Cannot ignore: system URN is missing");
      return;
    }

    const result = await muteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(`${systemName || "System"} has been ignored.`);
      if (onSuccess) {
        onSuccess();
      }
    }
  };

  const handleRestore = async () => {
    if (!urn) {
      messageApi.error("Cannot restore: system URN is missing");
      return;
    }

    const result = await unmuteIdentityProviderMonitorResultMutation({
      monitor_config_key: monitorId,
      urn,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(`${systemName || "System"} has been restored.`);
      if (onSuccess) {
        onSuccess();
      }
    }
  };

  return {
    ignore: {
      disabled: false,
      callback: handleIgnore,
      loading: isMuting,
      hidden: diffStatus === DiffStatus.MUTED,
    },
    restore: {
      disabled: false,
      callback: handleRestore,
      loading: isUnmuting,
      hidden: diffStatus !== DiffStatus.MUTED,
    },
    approve: {
      disabled: diffStatus === DiffStatus.MUTED,
      callback: handleApprove,
      loading: isPromoting,
      hidden: false,
    },
  };
};
