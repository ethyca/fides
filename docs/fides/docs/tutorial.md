# Tutorial

This tutorial walks you through the process of getting up and running with Fidesctl.

## Getting Started

Use either the [Docker](https://ethyca.github.io/fides/getting_started/docker/) (**recommended**) or [Local](https://ethyca.github.io/fides/getting_started/local/) guide to get Fidesctl up and running on your machine.

## Writing Manifest Files

The next step is to write the manifest files that describe your privacy data usage with the Fides privacy ontology. Manifest files are written in YAML and are used to create and update resources via the Fidesctl API.

First create a directory for the manifests to live in:

`mkdir fides_resources/`

Next, you'll need to write a System manifest file and a Policy manifest file. These are the only two required resources for Fidesctl to function. For an exhaustive set of example manifests see the [Fides Resources](https://ethyca.github.io/fides/fides_resources/) page. Included below are the examples we'll assume are being used for the sake of the tutorial.

=== fides_resources/policy.yml

    ```yaml
    policy:
      - organization_fides_key: 1
        fides_key: demo_privacy_policy
        name: Demo Privacy Policy
        description: The main privacy policy for the organization.
        rules:
          - organization_fides_key: 1
            fides_key: reject_direct_marketing
            name: Reject Direct Marketing
            description: Disallow collecting any user contact info to use for marketing.
            data_categories:
              inclusion: ANY
              values:
                - user.provided.identifiable.contact
            data_uses:
              inclusion: ANY
              values:
                - marketing_advertising_or_promotion
            data_subjects:
              inclusion: ANY
              values:
                - customer
            data_qualifier: identified_data
            action: REJECT
    ```

### fides_resources/dataset.yml

    ```yaml
    dataset:
      - organization_fides_key: 1
        fides_key: demo_users_dataset
        name: Demo Users Dataset
        description: Data collected about users for our analytics system.
        dataset_type: MySQL
        location: US East
        fields:
          - name: first_name
            description: User's first name
            path: demo_users_dataset.first_name
            data_categories:
              - user.provided.identifiable.name
          - name: email
            description: User's Email
            path: demo_users_dataset.email
            data_categories:
              - user.provided.identifiable.contact.email
          - name: state
            description: User's State
            path: demo_users_dataset.state
            data_categories:
              - user.provided.identifiable.contact.state
          - name: food_preference
            description: User's favorite food
            path: demo_users_dataset.food_preference
            data_categories:
              - user.provided.nonidentifiable
          - name: created_at
            description: User's creation timestamp
            path: demo_users_dataset.created_at
            data_categories:
              - system.operations
          - name: uuid
            description: User's unique ID
            path: demo_users_dataset.uuid
            data_categories:
              - user.derived.identifiable.unique_id
    ```

=== fides_resources/system.yml

    ```yaml
    system:
      - organization_fides_key: 1
        fides_key: demo_analytics_system
        name: Demo Analytics System
        description: A system used for analyzing customer behaviour.
        system_type: Service
        privacy_declarations:
          - name: Analyze customer behaviour for improvements.
            data_categories:
              - user.provided.identifiable.contact
              - user.derived.identifiable.device.cookie_id
            data_use: improve_the_product_or_service
            data_subjects:
              - customer
            data_qualifier: identified_data
            dataset_references:
              - demo_users_dataset

      - organization_fides_key: 1
        fides_key: demo_marketing_system
        name: Demo Marketing System
        description: Collect data about our users for marketing.
        system_type: Service
        privacy_declarations:
          - name: Collect data for marketing
            data_categories:
              # - user.provided.identifiable.contact # uncomment to add this category to the system
              - user.derived.identifiable.device.cookie_id
            data_use: marketing_advertising_or_promotion
            data_subjects:
              - customer
            data_qualifier: identified_data
    ```

## Applying Manifest Files

Once you've finished writing your manifest files, it's time to apply them to the server. This is done with a single `fidesctl` command that handles both creating _and_ updating resources. If a resource with the same type and fides_key already exists, that resource will be updated if a change has been made.

If we assume the same directory name as before for where our manifests are located, the command would be:

`fidesctl apply fides_resources/`

This will load all files ending in either `.yaml` or `.yml` within that directory. Any invalid resource definitions within the manifests will be caught and shown to the user.

## Evaluation

Systems and Registries have a slightly different workflow as they are also designed to be incorporated into CI pipelines.

Now that you've created your initial manifest files via the `apply` command, it's time to evaluate if that initial system is compliant. Use the following command to evaluate your system:

`fidesctl evaluate system demo_analytics_system`

If that command returns a PASS evaluation, then you're now in a known-good state and ready to set up automated CI workflows to make sure your application stays compliant with each PR.

## Setting up CI/CD

To set up CI/CD for Fides evaluations, there are a few suggested steps to follow:

### Pull Request

    1. Set up a new CI workflow that gets triggered whenever a system or registry file gets changed within a pull request.
    1. Configure the new workflow to run `fidesctl dry-evaluate fides_manifests/ <fides_key>` when it gets triggered.
    1. The command will trigger a non-zero exit if the evaluation fails.

    Use the result of this job to determine whether or not a system change is safe to merge or not. If the command fails, check the error messages to see why the evaluation failed.

### Merge Event

    1. Set up a new CI workflow that gets triggered whenever something in your manifests directory changes and the branch gets merged to the main branch.
    1. Configure the new workflow to run two few jobs:
        1. `fidesctl apply fides_manifest/`
        1. `fidesctl evaluate system <fides_key>`

    This will apply all of your manifests to the API and then evaluate the current state of your system on the main branch.

## Next Steps

Congratulations, you've walked through all of the steps to get a simple but complete Fidesctl instance running! Here are some possible next steps to continue building out your Fidesctl deployment:

1. Set up more Systems
1. Create a Registry to assign systems to
1. Extend the Privacy Classifiers as needed
1. Add additional Policy Rules
