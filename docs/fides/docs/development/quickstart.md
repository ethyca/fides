# Quickstart

This guide will walk you through building a local development environment to start contributing quickly! Be sure to review our [community guidelines](https://docs.ethyca.com/fides/community/overview) and happy hacking!

## Pre-requesites

1. Download the latest LTS for Node 16
2. Download the latest LTS for Python 3
3. We recommend making a python virtual environment in the repo and set the source to the repo

### Backend Setup
To get started working on the Fides backend, Ethyca recommends the following:

1. Install the requirements and dependencies `pip install -r requirements.txt`
2. Type `nox -s dev` to build a development backend
   - Helpful tip: type `nox` for more information on what other commands are available or navigate to [Developing Fides](https://ethyca.github.io/fides/dev/development/developing_fides/)
3. Once the environment is built, you need to add your first user.
4. Navigate to `localhost:8080/docs` to begin initial setup.
5. In the top right corner, click on Authorize and type in the default OAuth Client ID and Secret which can be found in `.fides/fides.toml`
6. After Authorizing,  you now need to make a user. Navigate to the `POST - /api/v1/user` endpoint and create your first user. Notate the user ID for the next steps
7. Navigate to the `PUT /api/v1/user/{user_id}/permission` endpoint and add the UserID to the parameter, and in the request body set the roles to owner. Press execute.
8. You have now created your first admin that you will log in to the UI with. 

### Frontend Setup
These steps are documented in the [Client/UI Development Guide](https://ethyca.github.io/fides/dev/development/clients/)