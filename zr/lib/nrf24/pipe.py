import asyncio
import queue
import logging


logger = logging.getLogger(__name__)

MAX_PAYLOAD_SIZE = 32


class BasePipe:
    _payload_length = None

    def __init__(self, radio, number):
        logger.debug('init {}'.format(number))
        self._radio = radio
        self.number = number

        self.enabled = False
        # self.address = 0
        self.payload_length = MAX_PAYLOAD_SIZE
        self.dynamic_payload = False
        self.auto_ack = False

    def receive_from_fifo(self, data):
        raise NotImplementedError

    def has_data(self):
        raise NotImplementedError

    def receive(self):
        raise NotImplementedError

    @property
    def enabled(self):
        return self._radio._registry['EN_RXADDR'][self.number]

    @enabled.setter
    def enabled(self, value):
        self._radio._registry['EN_RXADDR'][self.number] = value

    @property
    def address(self):
        return self._radio._registry['RX_ADDR_P' + str(self.number)]

    @address.setter
    def address(self, value):
        self._radio._registry['RX_ADDR_P' + str(self.number)] = value

    @property
    def payload_length(self):
        if self._payload_length is None:
            self._payload_length = self._radio._registry['RX_PW_P' + str(self.number)]

        return self._payload_length

    @payload_length.setter
    def payload_length(self, value):
        if 0 <= value <= MAX_PAYLOAD_SIZE:
            self._radio._registry['RX_PW_P' + str(self.number)] = value
            self._payload_length = value
        else:
            raise ValueError('0 <= {} <= {}'.format(value, MAX_PAYLOAD_SIZE))

    @property
    def dynamic_payload(self):
        return self._radio._registry['DYNPD'][self.number]

    @dynamic_payload.setter
    def dynamic_payload(self, value):
        self._radio._registry['DYNPD'][self.number] = value

    @property
    def auto_ack(self):
        return self._radio._registry['EN_AA'][self.number]

    @auto_ack.setter
    def auto_ack(self, value):
        self._radio._registry['EN_AA'][self.number] = value


class Pipe(BasePipe):
    _payload_length = None

    def __init__(self, radio, number, queue_size=1024):
        super().__init__(radio, number)
        self._queue = queue.Queue(maxsize=queue_size)

    def __repr__(self):
        return '<Pipe: {}>'.format(self.number)

    def receive_from_fifo(self, data):
        try:
            self._queue.put(data, block=False)
            return True
        except queue.Full:
            logger.warning(
                'queue pipe {} is full, lost {} bytes'.format(self.number, len(data)))
            return False

    def has_data(self):
        return not self._queue.empty()

    def receive(self):
        try:
            return self._queue.get(block=False)
        except self._queue.Empty:
            return None


class PipeAio(BasePipe):
    _payload_length = None

    def __init__(self, radio, number, queue_size=1024):
        super().__init__(radio, number)
        self._queue = asyncio.Queue(maxsize=queue_size)

    def __repr__(self):
        return '<Pipe: {}>'.format(self.number)

    def receive_from_fifo(self, data):
        try:
            self._queue.put_nowait(data)
            return True
        except asyncio.QueueFull:
            logger.warning(
                'queue pipe {} is full, lost {} bytes'.format(self.number, len(data)))
            return False

    def has_data(self):
        return not self._queue.empty()

    def receive(self):
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    @asyncio.coroutine
    def receive_coro(self):
        try:
            return (yield from self._queue.get())
        except asyncio.QueueEmpty:
            return None
