import { useRouter } from "next/router";

import { INDEX_ROUTE } from "~/constants";
import ErrorPage from "~/features/common/errors/ErrorPage";

const ErrorTest = () => {
  const router = useRouter();
  const errorTest = {
    status: 404,
    data: {
      detail: "We couldn't find your stuff.  Our bad!",
    },
  };
  return (
    <ErrorPage
      error={errorTest}
      actions={[
        {
          label: "Return home",
          onClick: () => {
            router.push(INDEX_ROUTE);
          },
        },
      ]}
    />
  );
};
export default ErrorTest;
