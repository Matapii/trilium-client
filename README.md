# Python Client for Trilium Note Manager

[Trilium Notes](https://github.com/zadam/trilium) is a note taking application. This repository provides a Python client to access and modify Trilium Notes content that is closely aligned with the [Trilium JavaScript Backend API](https://github.com/zadam/trilium/wiki/Script-API). 

The Python client communicates with Trilium Notes via a [custom request handler](https://github.com/zadam/trilium/wiki/Custom-request-handler), which must be installed first in the following way:

- Install `res/trilim_handler.js` as `#customRequestHandler="python-client"`
- Set `#pythonClientToken="..."` on this note

Basic Usage:
```
from trilium_client import *
client = Client('https://<trilium-host>/custom/python-client', <pythonClientToken>)
appInfo = client.getAppInfo()
currentNote = client.currentNote
client.searchForNotes('test', dict(limit=2, ancestorNoteId='yXqOlXJrvIvK'))
```

Note: Requires Trilium v0.48+

# Running the Tests

To run the tests, docker and docker-compose needs to be installed locally and calling docker should be possible without sudo.

```
$ poetry install
$ poetry shell
$ pytest --cov=trilium_client
```
