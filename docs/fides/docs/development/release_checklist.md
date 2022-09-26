# Release Checklist

## Documentation (`nox -s docs_serve`)

- [ ] Quickstart verified working and up-to-date
- [ ] Tutorial verified working and up-to-date
- [ ] Fidesdemo verified working and up-to-date
- [ ] New/updated API endpoints described in the Guides
- [ ] New/updated API endpoints included in the Postman collections
- [ ] New tables/columns added to database diagram

## Functionality (`nox -s dev -- shell` & local)

- [ ] Valid evaluation runs as expected, output is correct
- [ ] Invalid evaluation runs as expected, error output is correct
- [ ] In a new local directory, run `fides init`
- [ ] Parse the valid files in `.fides` (`fides parse /.fides`)

## UI (`nox -s dev` -- UI)

- [ ] Go to the system tab
  - [ ] Add a new system via the yaml ingestor
