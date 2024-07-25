import "../styles/globals.css";

import type { AppProps } from "next/app";

const App = ({ Component, pageProps }: AppProps) => (
  // @ts-expect-error Server Component
  <Component {...pageProps} />
);

export default App;
