# fidesctl-config-parser
## Features
- Parse your fidesctl manifest files to validate syntax
- Auto parsing of manifest files on save

## Commands
```
Fidesctl Parse
```

```
Fidesctl Configure Plugin
```

```
Fidesctl Enable Parse on Save
```

```
Fidesctl Disable Parse on Save
```

## Requirements

### Fidesctl

Install Fidesctl via pip

```
pip install fidesctl
```

You must also have a fidesctl server available to invoke the api
## Extension Settings
- "conf.fidesctl.confFilePath": Path of fidesctl.toml file which will be used to invoke the cli
- "conf.fidesctl.manifestFilePath": Path of fidesctl manifest files which the plugin will parse
- "conf.fidesctl.parseOnSave": Determines whether to parsing of manifest will be done on save
----------------------------------------------------------------------
