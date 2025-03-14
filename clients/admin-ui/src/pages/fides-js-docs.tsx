import "swagger-ui-react/swagger-ui.css";

import { NextPage } from "next";
import SwaggerUI from "swagger-ui-react";

// Only include API docs in development builds
export const getServerSideProps = () => {
  if (process.env.NODE_ENV !== "development") {
    return {
      notFound: true,
    };
  }
  return { props: {} };
};

const Docs: NextPage = () => <SwaggerUI url="/api/openapi.json" />;

export default Docs;
