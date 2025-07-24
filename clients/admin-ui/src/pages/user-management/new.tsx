import React from "react";
import NewUserForm from "user-management/NewUserForm";

import Layout from "~/features/common/Layout";

const CreateNewUser = () => (
  <Layout title="Users - New User">
    {/*
      We're going to have some problems with flow here. The NewUserForm no longer
      redirects to the user management table after a user is created since there
      are still roles to edit. But this means the user will still be on the
      NewUserForm and if they try to make edits they'll actually be making a new user!!

      We may need to do some thinking around the flow we want here, and maybe refactor
      these forms to work more like the way the SystemInformation form works, where the
      form itself figures out if it's creating or updating, rather than relying on its
      parents to tell it what to do.
    */}
    <NewUserForm />
  </Layout>
);

export default CreateNewUser;
