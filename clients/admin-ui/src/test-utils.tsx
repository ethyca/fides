// Mocks useRouter
const useRouter = jest.spyOn(require("next/router"), "useRouter");

/**
 * mockNextUseRouter
 * Mocks the useRouter React hook from Next.js on a test-case by test-case basis
 * Adapted from https://github.com/vercel/next.js/issues/7479#issuecomment-587145429
 */
// we will probably have more than just this in this utils file, so keep it as a non-default export for now
// eslint-disable-next-line import/prefer-default-export
export function mockNextUseRouter({
  route = "/",
  pathname = "/",
  query = "/",
  asPath = "/",
}: {
  route?: string;
  pathname?: string;
  query?: string;
  asPath?: string;
}) {
  useRouter.mockImplementation(() => ({
    route,
    pathname,
    query,
    asPath,
  }));
}
