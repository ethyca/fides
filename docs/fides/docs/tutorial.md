# Tutorial

This tutorial walks you through the process of getting up and running with Fides.

## Getting Started

Use either the [Docker](getting_started/docker.md) (**recommended**) or [Local](getting_started/local.md) guide to get Fides up and running on your machine.

## Writing Manifest Files

The next step is to write the manifest files that describe your privacy data usage with the Fides privacy ontology. Manifest files are written in YAML and are used to create and update resources via the FidesAPI.

First create a directory for the manifests to live in:

`mkdir fides_manifests/`

Next, you'll need to write a System manifest file and a Policy manifest file. These are the only two required resources for Fides to function. For an exhaustive set of example manifests see the [Fides Resources](fides_resources.md) page. Included below are the examples we'll assume are being used for the sake of the tutorial.

=== "fides_manifests/policy.yml"

    ```yaml
    policy:
      - organizationId: 1
        fides_key: "primaryPrivacyPolicy"
        name: "Primary Privacy Policy"
        description: "The main privacy policy for the organization."
        rules:
          - organizationId: 1
            fides_key: "rejectTargetedMarketing"
            name: "Reject Targeted Marketing"
            description: "Disallow marketing that is targeted towards users."
            dataCategories:
              inclusion: "ANY"
              values:
                - profiling_data
                - account_data
                - derived_data
                - cloud_service_provider_data
            dataUses:
              inclusion: ANY
              values:
                - market_advertise_or_promote
                - offer_upgrades_or_upsell
            dataSubjects:
              inclusion: ANY
              values:
                - trainee
                - commuter
            dataQualifier: pseudonymized_data
            action: REJECT
          - organizationId: 1
            fides_key: rejectSome
            name: "Reject Some Marketing"
            description: "Disallow some marketing that is targeted towards users."
            dataCategories:
              inclusion: ANY
              values:
                - user_location
                - personal_health_data_and_medical_records
                - connectivity_data
                - credentials
            dataUses:
              inclusion: ALL
              values:
                - improvement_of_business_support_for_contracted_service
                - personalize
                - share_when_required_to_provide_the_service
            dataSubjects:
              inclusion: NONE
              values:
                - trainee
                - commuter
                - patient
            dataQualifier: pseudonymized_data
            action: REJECT
    ```

### "fides_manifests/dataset.yml"

    ```yaml
    dataset:
      - organizationId: 1
        fides_key: "sample_db_dataset"
        name: "Sample DB Dataset"
        description: "This is a Sample Database Dataset"
        datasetType: "MySQL"
        location: "US East"
        fields:
          - name: "First_Name"
            description: "A First Name Field"
            path: "sample_db_dataset.first_name"
            dataCategories:
              - "derived_data"
            dataQualifier: "identified_data"
          - name: "Email"
            description: "User's Email"
            path: "sample_db_dataset.email"
            dataCategories:
              - "account_data"
            dataQualifier: "anonymized_data"
          - name: "Food_Preference"
            description: "User's favorite food"
            path: "sample_db_dataset.food_preference"
    ```

=== "fides_manifests/system.yml"

    ```yaml
    system:
      - organizationId: 1
        fides_key: "demoSystem"
        name: "Demo System"
        description: "A system used for demos."
        systemType: "Service"
        privacyDeclarations:
          - name: "Analyze Anonymous Content"
            dataCategories:
              - "account_data"
            dataUse: "provide"
            dataQualifier: "anonymized_data"
            dataSubjects:
              - "anonymous_user"
            datasetReferences:
              - "sample_db_dataset.Email"
        systemDependencies: []
    ```

## Applying Manifest Files

Once you've finished writing your manifest files, it's time to apply them to the server. This is done with a single `fidesctl` command that handles both creating _and_ updating resources. If a resource with the same type and fides_key already exists, that resource will be updated if a change has been made.

If we assume the same directory name as before for where our manifests are located, the command would be:

`fidesctl apply fides_manifests/`

This will load all files ending in either `.yaml` or `.yml` within that directory. Any file formatting issues within the manifests will be caught and shown to the user.

## Evaluation

Systems and Registries have a slightly different workflow as they are also designed to be incorporated into CI pipelines.

Now that you've created your initial manifest files via the `apply` command, it's time to evaluate if that initial system is compliant. Use the following command to evaluate your system:

`fidesctl evaluate system demoSystem`

If that command returns a "PASS" evaluation, then you're now in a known-good state and ready to set up automated CI workflows to make sure your application stays compliant with each PR.

## Setting up CI/CD

To set up CI/CD for Fides evaluations, there are a few suggested steps to follow:

### "Pull Request"

    1. Set up a new CI workflow that gets triggered whenever a system or registry file gets changed within a pull request.
    1. Configure the new workflow to run `fidesctl dry-evaluate fides_manifests/ <fides_key>` when it gets triggered.
    1. The command will trigger a non-zero exit if the evaluation fails.

    Use the result of this job to determine whether or not a system change is safe to merge or not. If the command fails, check the error messages to see why the evaluation failed.

### "Merge Event"

    1. Set up a new CI workflow that gets triggered whenever something in your manifests directory changes and the branch gets merged to the main branch.
    1. Configure the new workflow to run two few jobs:
        1. `fidesctl apply fides_manifest/`
        1. `fidesctl evaluate system <fides_key>`

    This will apply all of your manifests to the API and then evaluate the current state of your system on the main branch.

## Next Steps

Congratulations, you've walked through all of the steps to get a simple but complete Fides instance running! Here are some possible next steps to continue building out your Fides deployment:

1. Set up more Systems
1. Create a Registry to assign systems to
1. Extend the Privacy Classifiers as needed
1. Add additional Policy Rules
