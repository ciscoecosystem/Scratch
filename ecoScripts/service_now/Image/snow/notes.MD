## Code Structure

### File Structure
Since the application code is more complicated than a simple single-file script,
all the application code is in the directory `code`.
This directory also contains some utility code.
Then, the consumer code is in `code/app` and the ServiceNow connector script is in
`code/snow-table-parser`

#### Consumer code
##### `app.py`
The starting point for the consumer application. Creates two threads: a consumer thread
that constantly looks for messages on Kafka, and a APIC thread that manages refreshing
session cookies. Also sets up signal handling for SIGINT, allowing for entire process
to gracefully exit.
##### `app_threads.py`
Defines the threads that will run, containing the bulk of the logic.
`app.py` directly uses the `APICThread` and `ConsumerThread` classes.  
##### `apic.py`
Defines the `APIC` class. Provides a HTTP request interface with the a specified APIC
as well as utility functions to login, logout, etc.
##### `database.py`
Defines `Database` class. Provides functions to log relevant application state in
MongoDB.

### Imports
Currently, the application code is structured as a module using relative imports.
In the future, absolute imports can be used; however, then the execution must start from
the base directory in the absolute imports.  

For example, if in `app.py` we have
`from code.app.apic import APIC`, then we run the program as
`python -m code.app.apic` where the working directory is `Image`

If using relative imports we then have instead
`from .apic import APIC`. As long as the current working directory is a parent of
all the modules in the relative import, then we can run as
`python -m relpath.to.file.apic`
