import { AntAlert as Alert, AntLink as Link, AntTitle as Title } from "fidesui";

import ErrorLayout from "~/features/login/error-layout";

const SsoNotEnabled = () => {
  return (
    <ErrorLayout>
      <Alert
        showIcon
        type="error"
        message={<Title level={2}>SSO is not enabled</Title>}
        description={
          <>
            Request that your administrator configure{" "}
            <Link href="https://www.ethyca.com/docs/user-guides/security/sso-authentication">
              SSO Authentication
            </Link>{" "}
            or login another way.
          </>
        }
      />
    </ErrorLayout>
  );
};

export default SsoNotEnabled;
