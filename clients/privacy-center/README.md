# FidesOps Privacy Center

Privacy center for FidesOps. A web application built in Next.js with the FidesUI component library.

## Configuration

You may configure the appearance of this web application at build time by modifying the `config.json` file inside the `config` directory. You're able to control:

- The header of the document
- The descriptive text of the document
- Which actions are present
- The titles and descriptions of, and personally identifying information required by, each action

You can also add any CSS you'd like to the page by adding it to the `config.css` file inside the `config` directory.

Additionally, if you're handy with React and are feeling a little brave you can customize the entire application by modifying the TypeScript source code in `pages/index.tsx` and `components/RequestModal.tsx`.

### Configuring CSS

In order to modify the way your application appears visually, you can add custom css to the `config/config.css` file. For example, to change the application's font to Courier:

```css
* {
  font-family: Courier !important;
}
```

Additionally, because this application uses CSS variables, you can modify those CSS variables directly, rather than adding custom CSS.

The only caveat to this is that we need to do so in a way that overrides the CSS variables' original values so that we can avoid the complexity of modifying the JavaScript file that holds the base values.

Our recommendation is that you do so by using selector specificity, as in the following example:

```css
:root:root {
  /* Changes the text color to red */
  --chakra-colors-gray-600: #f00;

  /* Changes the background color to blue */
  --chakra-colors-gray-50: #00f;
}
```

Not exactly the most appealing color scheme – but note that wherever those variables are used, they have been replaced. This allows you to modify the theme of the application consistently and with a single source of truth, adhering to modern CSS best practices.

## Development

To serve this application locally, first install your local dependencies by running

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

To deploy this site, fork this repository. Then, configure a smart hosting service such as Vercel or Netlify to deploy it, specifying the root directory for the client application as the `clients/privacy-center` directory (relative to the root of the repository).
