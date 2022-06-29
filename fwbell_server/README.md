This is the current solution to the problem of only being able to run the wrapped libraries in 32 bit python.

there are two parts. The first is the FW Bell Server, and the other is the FW Bell client. The server is run in 32 bit python (currently tested using Python 3.9 32 bit using a portable WinPython distribution). It listens to 127.0.0.1 on port 65432 on a socket. It then executes the commands that are given to it. The commands must be sent from client to server (and back) in bytes - this is why there are lots of byte(cmd,'utf-8') commands, it is converting the cmd Python string into a byte string. The str(response,'utf-8') converts the byte string "response" into a normal python string. There are a few special commands:

command 1, by sending the following string:
"Client to server: attempting to connect" 
-- this simply causes the server to respond to the client with "Server to client: connected."

command 2:
"Client to server: killServer"
-- kills the FW Bell server.

command 3:
'isGaussmeterInitialized?'
-- responds with "yes" or 'no' to the question

command 4:
"closing"
-- closes the current connection to the client and waits to initialize another client connection.

Any other command is assumed to be something to be sent directly to the gaussmeter, i.e. "*IDN?" or ":MEASURE:FLUX?".

Note that there is a check using usb.core if the specific gaussmeter is connected. So, you may need to change the appropriate line in the iniatialize_gaussmeter function.

Run the server first. Then run the client. The server code is written to be able to disconnect and reconnect to a client (using the "closing" command).

The client side software is simply provided as an example, and you may need to repurpose it to your needs. A simple example is provided.


