import socket

from alter_igo import create_app

app = create_app()

host = socket.gethostbyname(socket.gethostname())
if __name__ == '__main__':
    app.run(debug=True, host=host, port=5000)