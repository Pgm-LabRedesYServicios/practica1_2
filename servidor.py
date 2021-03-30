import select
import socket
import sys


# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
server_address = ('', 10000)
print('starting up on {} port {}'.format(*server_address),
              file=sys.stderr)
server.bind(server_address)

# Listen for incoming connections
server.listen(5)

# Sockets from which we expect to read
inputs = [server]




#Bucle para bloquear y esperar actividad de la red
while inputs:

        # Wait for at least one of the sockets to be
        # ready for processing
    print('waiting for the next event', file=sys.stderr) 
    readable, writable, exceptional = select.select(inputs, [], [])

    # Esta seccion establece que el conector del cliente no se bloquee

    # Handle inputs
    for s in readable:
        if s is server:
            # A "readable" socket is ready to accept a connection
            connection, client_address = s.accept()
            print('  connection from', client_address, file=sys.stderr) 
            connection.setblocking(0)
            inputs.append(connection)

        


#los datos se leen con recv(), se colocan  en cola para que puedan ser enviados a traves del conector y de vuelta al cliente

        else:
            data = s.recv(1024)
            if data:
                # A readable client socket has data
                print('  received {!r} from {}'.format(
                    data, s.getpeername()), file=sys.stderr,
                )
                for p in inputs:
                    if p is not server:
                        if p is not s:
                            p.sendall(data)
                    

            else:
                # Interpret empty result as closed connection
                print('  closing', client_address,
                file=sys.stderr)
                # Stop listening for input on the connection
                inputs.remove(s)
                s.close()

                    #

#Si hay datos en la cola para una conexión, se envía el siguiente mensaje. De otra manera, la conexión se elimina de la lista de conexiones de salida para que la próxima vez a través del bucle select() no indique que el conector está listo para enviar datos.


    

#Para acabar, si hya un error con un conector, se cierra

    # Handle "exceptional conditions"




