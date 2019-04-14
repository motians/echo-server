"""
Server socket for multi client connections
"""

import socket
import sys
import traceback
import select
import queue


def server(log_buffer=sys.stderr):
    # set an address for our server
    address = ('127.0.0.1', 10000)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # log that we are building a server
    print("making a server on {0}:{1}".format(*address), file=log_buffer)

    sock.bind(address)
    sock.listen(5)

    inputs = [sock]
    outputs = []
    message_queues = {}

    try:
        # the outer loop controls the creation of new connection sockets. The
        # server will handle each incoming connection one at a time.
        while inputs:

            read_server, write_server, excep_server = select.select(inputs, outputs, [])

            for s in read_server:
                if s is sock:
                    conn, addr = s.accept()
                    print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                    conn.setblocking(0)
                    inputs.append(conn)
                    message_queues[conn] = queue.Queue()
                else:
                    # Collecting 16 bytes of data at a time
                    data = s.recv(16)
                    if data:
                        print('Received: {}'.format(data), file=log_buffer)
                        message_queues[s].put(data)
                        if s not in outputs:
                            outputs.append(s)
                        break
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        print('Closing conn - {0}:{1}'.format(*addr), file=log_buffer)
                        s.close()
                        del message_queues[s]

            for s in write_server:
                try:
                    next_msg = message_queues[s].get_nowait()
                    print('Sending: {}'.format(next_msg), file=log_buffer)
                except queue.Empty:
                    outputs.remove(s)
                else:
                    s.send(next_msg)

            for s in excep_server:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

    except Exception as e:
        traceback.print_exc()
        print(f'Exception: {e}')
        sock.close()
        print('quitting echo server', file=log_buffer)


if __name__ == '__main__':
    server()
    sys.exit(0)
