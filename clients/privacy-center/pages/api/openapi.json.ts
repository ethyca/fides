import { withSwagger } from "next-swagger-doc";

// Only include API docs in development builds
export const getServerSideProps = () => {
  if (process.env.NODE_ENV !== "development") {
    return {
      notFound: true,
    };
  }
  return { props: {} };
};

/**
 * @swagger
 * /openapi.json:
 *   get:
 *     description: Returns the OpenAPI schema for the Fides Privacy Center server
 */
const swaggerHandler = withSwagger({
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Fides Privacy Center API",
      version: process.env.version!,
    },
    servers: [
      {
        url: "http://localhost:3000",
        description: "Dev server",
      },
    ],
  },
  apiFolder: "pages/api",
});

export default swaggerHandler();
