import { usePostPrivacyRequestFinalizeMutation } from "~/features/privacy-requests";

export const useFinalizePrivacyRequest = () => {
  const [finalizeRequest, { isLoading }] =
    usePostPrivacyRequestFinalizeMutation();

  const handleFinalize = async (id: string) => {
    await finalizeRequest({ privacyRequestId: id });
  };

  return {
    isLoading,
    handleFinalize,
  };
};
