import time
import enum
# from contextlib import contextmanager
import logging

import spidev
from quick2wire.gpio import Out, pi_header_1

from zr.lib.nrf24.registry import Registry
from zr.lib.nrf24.pipe import Pipe
from zr.lib.nrf24.mnemonic import *


logger = logging.getLogger(__name__)


MAX_CHANNEL = 127


def _acquire_csn(meth):
    def wrapper(self, *args, **kwargs):
        self._csn.value = 0
        time.sleep(0.001)
        logger.debug('CSN = 0')
        res = meth(self, *args, **kwargs)
        self._csn.value = 1
        time.sleep(0.001)
        logger.debug('CSN = 1')
        return res

    return wrapper


def _check_status(*statuses):
    def wrapper(meth):
        def wrapperwrapper(self, *args, **kwargs):
            if self.status in statuses:
                res = meth(self, *args, **kwargs)
                return res
            else:
                raise RuntimeError('bad status: {!s}'.format(self.status))

        return wrapperwrapper
    return wrapper


class TX:
    def __init__(self, radio, pipe):
        self._radio = radio
        self._pipe = pipe
        self._csn = radio._csn
        self._radio._registry['TX_ADDR'] = radio.pipe(pipe).address
        self._payload_size = radio._registry['RX_PW_P' + str(pipe)]

    def write(self, data, no_ack=False):
        if isinstance(data, str):
            data.encode(data)

        ps = self._payload_size

        for n in range((len(data) // ps) + 1):
            payload_data = list(data[ps*n:ps*n+ps])

            if not payload_data:
                break
            elif len(payload_data) < ps:
                payload_data = [0x00]*(len(payload_data) - ps) + payload_data

            if no_ack:
                cmd = W_TX_PAYLOAD_NO_ACK
            else:
                cmd = W_TX_PAYLOAD

            self._radio._csn.value = 0
            payload = [cmd] + payload_data
            self._radio._spi.xfer(payload)
            self._radio._csn.value = 1

    @_acquire_csn
    def flush(self):
        self._csn = self._radio._csn
        self._radio._spi.xfer([FLUSH_TX])

    @property
    def empty(self):
        return self._radio._registry['FIFO_STATUS']['TX_EMPTY']

    @property
    def full(self):
        return self._radio._registry['FIFO_STATUS']['TX_FULL']


class NRF24:
    @enum.unique
    class STATUS(enum.Enum):
        power_down = 1
        stand_by = 2
        rx = 3
        tx = 4

    def __init__(self, csn, ce, spi_major=0, spi_minor=0):
        self._spi = spidev.SpiDev()
        self._spi.open(spi_major, spi_minor)
        self._csn = pi_header_1.pin(csn, direction=Out)
        self._ce = pi_header_1.pin(ce, direction=Out)

        self._registry = Registry(self)

        self._status = NRF24.STATUS.power_down

        # load defaults
        with self:
            self._registry['STATUS'] = 0b01110000
            self._registry['CONFIG'] = 0b00001010
            self._registry['EN_AA'] = 0b00000000
            self._registry['EN_RXADDR'] = 0b00000000
            self._registry['SETUP_AW'] = 0b00000011
            self._registry['SETUP_RETR'] = 0b00000011
            self._registry['RF_CH'] = 2
            self._registry['RF_SETUP'] = 0b0000111
            self._registry['DYNPD'] = 0b00000000
            self._registry['FEATURE'] = 0b00000000
            self._registry['TX_ADDR'] = 0xe7e7e7e7e7
            self._registry['RX_ADDR_P0'] = 0xe7e7e7e7e7
            self._registry['RX_PW_P0'] = 32

            self.pipes = {
                0: Pipe(self, 0, queue_size=4),
                1: Pipe(self, 1, queue_size=4),
                2: Pipe(self, 2, queue_size=4),
                3: Pipe(self, 3, queue_size=4),
                4: Pipe(self, 4, queue_size=4),
                5: Pipe(self, 5, queue_size=4),
            }

    def __enter__(self):
        try:
            if self._csn.closed:
                self._csn.open()
                self._csn.value = True

            if self._ce.closed:
                self._ce.open()
                self._ce.value = False
        except:
            import os
            os.system('gpio-admin unexport 7; gpio-admin unexport 8;')
            raise

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.status != NRF24.STATUS.power_down:
                self.status = NRF24.STATUS.power_down

            self._ce.value = False
            self._csn.value = True

            if exc_type is not None:
                self.close()

        except Exception as exc:
            import os
            os.system('gpio-admin unexport 7; gpio-admin unexport 8;')
            print(type(exc), exc)
            raise

    def close(self):
        time.sleep(0.1)
        self._ce.close()
        time.sleep(0.1)
        self._csn.close()

    @_acquire_csn
    def _read_register(self, reg, blen=1):
        """ Low level read register
        """
        buf = [R_REGISTER | (REGISTER_MASK & reg)]
        buf += [NOP] * max(1, blen)

        data = self._spi.xfer(buf)[1:]
        logger.debug('read registry {}, {} => {}'.format(reg, buf, data))
        return data

    @_acquire_csn
    def _write_register(self, reg, value, length=1):
        """ Low level write register
        """
        buf = [W_REGISTER | (REGISTER_MASK & reg)]

        for i in range(length, 0, -1):
            buf.append(value & 0xff)
#             buf.insert(1, value & 0xff)
            value >>= 8
            i -= 1

        self._spi.xfer(buf)
        logger.debug('write registry {}, {}'.format(reg, buf))

    @property
    def channel(self):
        """ Property for get and set current rf channel
        """
        return int(self._registry['RF_CH'])

    @channel.setter
    @_check_status(STATUS.stand_by)
    def channel(self, value):
        if not 0 <= value <= MAX_CHANNEL:
            raise ValueError('0 <= {} <= {}'.format(0, value, MAX_CHANNEL))

        self._registry['RF_CH'] = value

    @property
    def status(self):
        """ Property for get and set device status

        It's middle level api and not recomendated for use dirrectly.
        """
        return self._status

    @status.setter
    def status(self, status):
        logger.debug('set status={}'.format(status))
        getattr(self, '_set_status_{!s}'.format(str(status).split('.', 1)[1]))()

    @_check_status(STATUS.stand_by, STATUS.rx, STATUS.tx)
    def _set_status_power_down(self):
        if self.status in (NRF24.STATUS.rx, NRF24.STATUS.tx):
            self.status = NRF24.STATUS.stand_by

        self._registry['CONFIG']['PWR_UP'] = False
        self._status = NRF24.STATUS.power_down

    @_check_status(STATUS.power_down, STATUS.rx, STATUS.tx)
    def _set_status_stand_by(self):
        old = self.status
        self._registry['CONFIG']['PWR_UP'] = True
        self._ce.value = False
        self._status = NRF24.STATUS.stand_by

        if old == NRF24.STATUS.power_down:
            time.sleep(0.0015)
        elif old in (NRF24.STATUS.rx, NRF24.STATUS.tx):
            time.sleep(0.00013)

    @_check_status(STATUS.power_down, STATUS.stand_by)
    def _set_status_tx(self):
        if self.status == NRF24.STATUS.power_down:
            self.status = NRF24.STATUS.stand_by

        self._registry['CONFIG']['PRIM_RX'] = False
        self._ce.value = True
        time.sleep(0.00002)
        self._status = NRF24.STATUS.tx

    @_check_status(STATUS.power_down, STATUS.stand_by)
    def _set_status_rx(self):
        if self.status == NRF24.STATUS.power_down:
            self.status = NRF24.STATUS.stand_by

        self._registry['CONFIG']['PRIM_RX'] = True
        self._ce.value = True
        self._status = NRF24.STATUS.rx

    def listening(self):
        self.status = NRF24.STATUS.rx

    @_acquire_csn
    def _read_from_rx_fifo(self):
        status = self._spi.xfer([R_RX_PAYLOAD])[0]
        pipe_number = (status >> 1) & 0b111  # get STATUS/RX_P_NO

        if pipe_number < 7:
            pipe = self.pipes[pipe_number]
            data = self._spi.xfer([NOP] * pipe.payload_length)
            logger.debug(
                '_read_from_rx_fifo: {} bytes for pipe {}'.format(len(data), pipe.number))
            return pipe, bytes(data)
        else:
            logger.debug('_read_from_rx_fifo: no data')
            return None, None

    def read_rx_fifo(self, count=3):
        """ This method read from radio rx fifo and send data to pipes
        """
        res = False

        for _ in range(count):
            pipe, data = self._read_from_rx_fifo()
            if pipe is not None:
                pipe.receive_from_fifo(data)
            else:
                break

        return res

    # @_check_status(STATUS.stand_by)
    # @contextmanager
    # def tx(self, pipe):
    #     """ Go into TX mode
    #     """
    #     last, self.status = self.status, NRF24.STATUS.tx
    #     yield TX(self, pipe)
    #     self.status = last
