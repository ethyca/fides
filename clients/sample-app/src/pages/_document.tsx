import Document, {
  DocumentContext,
  DocumentInitialProps,
  Head,
  Html,
  Main,
  NextScript,
} from "next/document";

/**
 * Define a custom Document, so that we can load external stylesheets, scripts, etc.
 * See https://nextjs.org/docs/pages/building-your-application/routing/custom-document
 */
class SampleAppDocument extends Document {
  static async getInitialProps(
    ctx: DocumentContext,
  ): Promise<DocumentInitialProps> {
    const initialProps = await Document.getInitialProps(ctx);
    return initialProps;
  }

  render() {
    return (
      <Html>
        <Head>
          <meta
            name="description"
            content="Sample Project used within Fides (github.com/ethyca/fides)"
          />
          <link rel="icon" href="/favicon.ico" />
          <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default SampleAppDocument;
