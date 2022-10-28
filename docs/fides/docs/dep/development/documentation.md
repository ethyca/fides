# Documentation

Documentation is an incredibly important part of Fides, both for explaining its concepts to general audiences and describing its usage to developers.

## Concepts

Fides includes a great deal of "concept" documentation, which covers features, tutorials, guides, and examples separately from the auto-generated API reference. 

To write concept docs, add Markdown files to the `docs/fides/docs/` directory (or one of its subdirectories). To ensure that your page is displayed in the navigation, edit `mkdocs.yml` to include a reference to it.

## Semantics

### Capitalization

Concepts that refer to proper nouns or are trademarked should always be capitalized. The exception for Fides is only when referencing any languages or tools, such as fideslang or fideslog.

Other Fides terms, like "Data Category" or "System", should also be capitalized to be clear about the fact that a Fides resource is being referenced.

> When a System is applied, it is either created or updated through the Fides api.

> The System model requires a field called `fides_key`.

## Previewing docs locally

Documentation (including both concepts and API references) is built and deployed with every merge to Fides's master branch.

If you're using VS Code Dev Containers, the docs will automatically be available at `localhost:8000`, otherwise you'll need to run the following command:

```bash
nox -s docs_serve
```

You'll see a status update as the docs build, and then an announcement that they are available on `http://127.0.0.1:8000`.
