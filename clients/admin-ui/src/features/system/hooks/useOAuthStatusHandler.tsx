import { useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useEffect } from "react";

interface UseOAuthStatusHandlerProps {
  setActiveTab: (tab: string) => void;
}

/**
 * Custom hook to handle OAuth status parameters in the URL.
 * When a status parameter is present (e.g., ?status=succeeded), this hook:
 * 1. Navigates to the integrations tab
 * 2. Shows appropriate toast message
 * 3. Cleans up the URL by removing the status parameter
 *
 * The status is automatically processed only once since the URL update removes
 * the status parameter, preventing the effect from running again.
 */
const useOAuthStatusHandler = ({
  setActiveTab,
}: UseOAuthStatusHandlerProps) => {
  const router = useRouter();
  const message = useMessage();

  useEffect(() => {
    const { status } = router.query;
    if (status && router.isReady) {
      // Set active tab to integrations
      setActiveTab("integrations");

      // Show appropriate toast message
      if (status === "succeeded") {
        message.success("Integration successfully authorized.");
      } else {
        message.error("Failed to authorize integration.");
      }

      // Single URL update: remove status query and add integrations hash
      const newQuery = { ...router.query };
      delete newQuery.status;

      router.replace(
        {
          pathname: router.pathname,
          query: newQuery,
          hash: "integrations",
        },
        undefined,
        { shallow: true },
      );
    }
  }, [router.query, setActiveTab, router, message]);
};

export default useOAuthStatusHandler;
