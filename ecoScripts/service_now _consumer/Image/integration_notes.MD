## Code Structure

### Docker Image

#### Docker
The Dockerfile should be relatively straightforward. The current build downloads python3.6 and then creates a virtual environment.  I add the virtual environment to PATH so that `python` refers to the virtual environment.

Following previous ecohub convention, the Docker image entrypoint is
`python eco_action.py`

The `ACTION` environment variable is set by ecohub.  There are three actions currently also defined in `service_now-0.1.json`, which are TEST_SNOW_CONNECTIVITY, TEST_ACI, and TEST_KAFKA_CONNECTIVITY.  

Since these actions are a subset of validating the whole integration config, I have included all these function in `validate.py`.  I used a simple `sys.argv` to pass in command line args to specify which action to take, where no command line args validates everything.  We might want to restructure this file.  It works, but it is just not pretty.

The main reason is that we cannot send a success message inside the indivdual tests for SNOW, ACI, KAFKA, because in the comprehensive test, we cannot be outputting to STDOUT until we know all three tests passed.  So, the scheme is a bit weird right now. I am not sure if there is a prettier solution
if we want code reusability, where the comprehensive test can call the individual tests.

### File Structure
Since the application code is more complicated than a simple single-file script,
all the application code is in the directory `code`.
This directory also contains some utility code.

##### Logging
This includes a modified logging class that formats inout into Pigeon format and outputs to stdout.  This class is not used in `eco_action.py` but this can be considered.  Currently, it uses `pigeon.py` to help send formatted messages to stdout.

If we decide to continues with the Logger wrapper class that I am currently using, we might want to add a custom logging level.  Pigeon returns a status code of 100 for standard info logs.  Thus, my logging class sets the status code to 100 for info level logs.  Please verify, but I believe that a 'success' info that signals the container finished its job, needs a 200 status code.  Therefore we cannot use the standard 'info' logging level and need a custom one.  Currently I am converting 'CRITICAL' level into 200 as a placeholder.

#### Consumer code
The consumer code is in `code/app` and the ServiceNow connector script is in
`code/snow-table-parser`

##### `app.py`
The starting point for the consumer application. Creates two threads: a consumer thread
that constantly looks for messages on Kafka, and a APIC thread that manages refreshing
session cookies. Also sets up signal handling for SIGINT, allowing for entire process
to gracefully exit.

Due to implementation of the Global Interpreter Lock in Cython, the threads are not parallelized;
however, since the APIC thread performs brief action and then sleeps for a couple minutes, and the
consumer thread is waiting for Kafka messages, performance should still be good.

The main reason I am using a lock is because I have two threads that both create `apic.APIC` object.  I want to make sure that they do not
call `apic.APIC.get_apic()` at the same time; then they will have different HTTP sessions.  The lock ensures that both threads get the same `apic.APIC` instance.

I also have a `threading.Event` object.  I am not sure if this is still relevant as we move to ecohub but I believe it can still be useful.
The way it is being used is: if we get some message or condition (currently, there is a signal handler that catches SIGINT), then we can call `threading.Event.set()`.  

The `APICThread` waits on this event.  Additionally, the `ConsumerThread` also keeps looping as long as the event is not set.
Therefore, if we receive SIGINT (or in the future some other signaling mechanism), we can gracefully terminate the script.

##### `app_threads.py`
Defines the threads that will run, containing the bulk of the logic.
`app.py` directly uses the `APICThread` and `ConsumerThread` classes.  

These thread classes subclass the python thread.Thread class.  Overriding the `run()`
method to set behavior of the thread.  This method is run when `start()` is called, which
starts the thread.

The current scope of the SNOW integration, this thread setup might be slightly overkill, but shouldn't
be bad, just a bit more code.

The basic flow of the `process_<action>_message()` methods is the same.
First, we check if we are creating/updating or deleting.
Then, if creating/updating, we query the DB to see if there is existing config, and what it is.

Then we perform the necessary steps to update relevant docs in DB and push changes to APIC.

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

### Improvements
Some of the code is still a bit 'hacky' in the sense I have not fully refined all of the code.  Some examples are some of the methods in `database.py` and the APIC functions defined in the bottom of `app_threads.ConsumerThread`.  We probably want to cleanup some of the
option parameters to these functions that I defined.  For example, here is the signature of the method that sends the API request to create a contract.
`create_contract(self, tenant, contract, filter, action, status='created,modified', delete=False)`

Currently, the `delete` parameter is determining whether we create or delete, with defauly being `delete`.  Additionally, I believe `status` is now extraneous and should be removed.

Finally, the consumer script is using `kafka-python` while the producer is using `pykafka`.  Both libraries should work, but it might be better to consolidate to one, reducing confusion.
