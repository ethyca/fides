import ErrorPage from "~/features/common/errors/ErrorPage";

const ErrorTest = () => {
  const errorTest = {
    status: 404,
    data: {
      detail: "This is a test error",
    },
  };
  return <ErrorPage error={errorTest} actions={[]} />;
};

export default ErrorTest;
