from PyQt6.QtNetwork import QTcpSocket, QAbstractSocket
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from collections import deque

DEBUG = True

class Client_qt(QObject):
    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    def __init__(self, host,port, interval_ms :int = 1500, parent=None):
        super().__init__(parent)
        self.host=host
        self.port=port
        self.interval_ms = interval_ms
        self._buffer = bytearray()
        self.socket = QTcpSocket(self)
        self.doconnect=False
        self._inflight = None
        self._queue = deque()

        self.socket.connected.connect(self._on_connected)
        self.socket.disconnected.connect(self._on_disconnected)
        self.socket.readyRead.connect(self._on_readyRead)
        self.socket.errorOccurred.connect(self._on_error)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(self.interval_ms)
        self.poll_timer.timeout.connect(self._poll)

        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.setInterval(2000)
        self.reconnect_timer.timeout.connect(self._connect)


    def start(self):
        self.doconnect = True
        self._connect()

    def stop(self):
        self.doconnect=False
        self.poll_timer.stop()
        self.reconnect_timer.stop()
        self.socket.disconnectFromHost()

    def send(self,data:bytes):
        if self.socket.state() == QAbstractSocket.SocketState.ConnectedState:
            print(data)
            self.socket.write(data)

    def _poll(self):
        self.send(b"1;pollAll")

    def _connect(self):
        if self.socket.state() == QAbstractSocket.SocketState.UnconnectedState:
            self.status_changed.emit(f"Connecting to {self.host}:{self.port}")
            self.socket.connectToHost(self.host,self.port)

    def _send_next(self):
        if (self._inflight is None and self._queue and self.socket.state() == QAbstractSocket.SocketState.ConnectedState):
            self._inflight = self._queue.popleft()
            if DEBUG:
                print("SENT", repr(self._inflight))
            self.socket.write(self._inflight)
            

    @pyqtSlot()
    def _on_connected(self):
        self.status_changed.emit("Connected")
        self._buffer.clear()
        self.poll_timer.start()
        self._poll()

    @pyqtSlot()
    def _on_disconnected(self):
        self.poll_timer.stop()
        self.status_changed.emit("Disconnected")
        if self.doconnect:
            self.reconnect_timer.start()

    @pyqtSlot()
    def _on_readyRead(self):
        self._buffer += self.socket.readAll().data()
        while (idx := self._buffer.find(b'!')) != -1:
            line = bytes(self._buffer[:idx]).decode(errors='replace')
            del self._buffer[:idx+1]
            if DEBUG:
                print(line)
            self.line_received.emit(line)

    @pyqtSlot(QAbstractSocket.SocketError)
    def _on_error(self):
        self.status_changed.emit(f"Error: {self.socket.errorString()}")
        if self.doconnect and self.socket.state == QAbstractSocket.SocketState.UnconnectedState:
            self.reconnect_timer.start()
