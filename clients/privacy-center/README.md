# FidesOps Privacy Center

Privacy center for FidesOps. A web application built in Next.js with the FidesUI
component library.

## Configuration

You may configure the appearance of this web application at build time by modifying the `config.json` file inside the `config` directory. You're able to control:

- The header of the document
- The descriptive text of the document
- Which actions are present
- The titles and descriptions of, and personally identifying information required by, each action

You can also add any CSS you'd like to the page by adding it to the `config.css`
file inside the `config` directory.

Additionally, if you're handy with React and are feeling a little brave you can
customize the entire application by modifying the TypeScript source code in
`pages/index.tsx` and `components/RequestModal.tsx`.

## Development

To serve this application locally, first install your local depencies by running

```bash
npm install
```

Then, run:

```bash
npm run dev
```

## Building

To build this application, run:

```bash
npm run build
```

As a Next application, it will output build artifacts to the `.next` directory.

## Testing

To run the interactive test interface, run:

```bash
npm run test
```

## Deployment

To deploy this site, fork this repository. Then, configure a smart hosting
service such as Vercel or Netlify to deploy it, specifying the root directory
for the client application as the `clients/privacy-center` directory (relative
to the root of the repository).
