# Admin UI

We include some user-related endpoints for the Fidesops Admin UI. In this section, we'll cover:

- I need permissions to be able to create a user. So how do I create the first user?
- How do I create other users?
- How do I log in and log out?



## Creating the first user

To create the first user, run the following `make` command:

`make user`

After supplying a name and suitable password, this will create an Admin Root UI User that you can use to login and create other users.


## Logging in

`POST api/v1/login` with your username and password in the request, and you will be issued a token with all scopes (for now)
that can be used to make subsequent requests.

```json
{
  "username": "test_username",
  "password": "Suitablylongwithnumber8andsymbol$"
}
```


## Logging out 

`POST api/v1/logout` with the user token as your Bearer Token.  This token will be invalidated (by deleting the associated client).


## Creating users

`POST api/v1/user` with a token that has `user:create` scope, with your username and password in the request body.

```json
{
  "username": "test_username",
  "password": "Suitablylongwithnumber8andsymbol$"
}
```

## Deleting users

`DELETE api/v1/user/<user_id>` with a token that has `user:delete` scope. Additionally, you must either be the  Admin Root UI User
or the user you're trying to delete.