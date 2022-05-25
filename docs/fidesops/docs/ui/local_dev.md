
## Local Development

To test the UI locally, clone the [FidesOps repository](https://github.com/ethyca/fidesops/), and ensure you have [Node.js](https://nodejs.org/en/download/) installed to run the application.
### Creating the root user

In the top-level `fidesops` directory, run `make user`.

A series of prompts will walk you through creating a username and password. Passwords require 8 or more characters, upper and lowercase characters, a number, and a symbol. 

This will create an Admin UI Root User that can be used to access additional [user endpoints](#managing-users).

### Accessing the Control Panel

From the root `fidesops` directory, run the following:
``` sh
    cd clients/admin-ui
    npm install
    npm run dev
```

This will navigate you to the `admin-ui` directory, and run the development environment.

Visit `http://localhost:3000/` in your browser, and provide your user credentials to log in. 

## Authentication

To enable stable authentication you must supply a `NEXTAUTH_SECRET` environment
variable. The best way to do this is by creating a `.env.local` file, which Next
will automatically pick up:

```bash
echo NEXTAUTH_SECRET=`openssl rand -base64 32` >> .env.local
```