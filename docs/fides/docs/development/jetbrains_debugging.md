<<<<<<< HEAD:docs/fides/docs/development/jetbrains_debugging.md
# Debugging Fides in IntelliJ IDEA Ultimate
This guide will show how to use the IntelliJ debugger with Fides running in Docker. 
=======
# Debugging fidesops in IntelliJ IDEA Ultimate
This guide will show how to use the IntelliJ debugger with fidesops running in Docker. 
>>>>>>> unified-fides-2:docs/fidesops/docs/development/jetbrains_debugging.md
The setup for PyCharm Professional should be very similar.

## Prerequisites
- [Intellij IDEA Ultimate](https://www.jetbrains.com/idea/buy/#commercial) or [PyCharm Professional](https://www.jetbrains.com/pycharm/buy/#commercial)
- [Docker plugin](https://plugins.jetbrains.com/plugin/7724-docker)
- [Python plugin](https://plugins.jetbrains.com/plugin/631-python) *(this is needed for Intellij)*
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
<<<<<<< HEAD:docs/fides/docs/development/jetbrains_debugging.md
=======
- [Fidesops](https://ethyca.github.io/fidesops/tutorial/installation/)
>>>>>>> unified-fides-2:docs/fidesops/docs/development/jetbrains_debugging.md

## Setup
### Connect to Docker daemon

This step will allow the IDE to connect to Docker Desktop.

Go to: **Settings/Preferences** -> **Docker** -> **+**

* Select **Docker for "your operating system"** 

See the screenshot below:

![Screenshot of IDE Docker setup](../img/ide/docker.png)

### Configure Python Remote Interpreter

Define a Docker-based remote interpreter.

Go to: **File** -> **Project Structure...** -> **Platform Settings** -> **SDKs** -> **+**

* Set **Server** to `Docker`
* Set **Configuration files** to `.docker-compose.yml`
* Set **Python interpreter path** to `python`

After clicking **OK** the Remote Python Docker Compose should be listed as an SDK.

See screenshots below:

![Screenshot of Add Python Interpreter](../img/ide/add_python_interpreter.png)

![Screenshot of Project Structure SDKs](../img/ide/SDKs.png)

### Run/Debug Configuration

Set up a Run/Debug Configuration so that breakpoints can be hit in the f sourcecode. 

Go to: **Run/Debug Configurations** -> **+** -> **Python**

<<<<<<< HEAD:docs/fides/docs/development/jetbrains_debugging.md
- To debug Fides, debug the `<path on your machine>/src/fides/main.py` script
- Make sure to select **Use specified interpreter** set the Remote Python Docker Compose *(created in the previous section)*
- Add `FIDES__CONFIG_PATH=/fides` to **Environment variables**
=======
- To debug fidesops, debug the `<path on your machine>/src/fidesops/main.py` script
- Make sure to select **Use specified interpreter** set the Remote Python Docker Compose *(created in the previous section)*
- Add `FIDES__CONFIG_PATH=/fidesops` to **Environment variables**
>>>>>>> unified-fides-2:docs/fidesops/docs/development/jetbrains_debugging.md

See screenshot below:

![Screenshot of Run/Debug Configuration for main.py](../img/ide/debug_config.png)

## Hit a Breakpoint

Now the IDE is ready to debug the source code. Click the debug button for **main** *(setup in the previous section)*.

<<<<<<< HEAD:docs/fides/docs/development/jetbrains_debugging.md
Try firing a http request to Fides from Postman or Curl and hit a break point. 

There is a postman collection in this repo: `docs/fides/docs/development/postman/Fides.postman_collection.json`
=======
Try firing a http request to fidesops from Postman or Curl and hit a break point. 

There is a postman collection in this repo: `docs/fidesops/docs/postman/Fidesops.postman_collection.json`
>>>>>>> unified-fides-2:docs/fidesops/docs/development/jetbrains_debugging.md

Screenshot of hit breakpoint below:

![Screenshot of Debugging from IntelliJ](../img/ide/debugging.png)

## Links

The information is this guide is largely based on these docs

- https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html
<<<<<<< HEAD:docs/fides/docs/development/jetbrains_debugging.md
- https://www.jetbrains.com/help/idea/configuring-local-python-interpreters.html
=======
- https://www.jetbrains.com/help/idea/configuring-local-python-interpreters.html
>>>>>>> unified-fides-2:docs/fidesops/docs/development/jetbrains_debugging.md
