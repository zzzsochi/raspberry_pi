from collections import namedtuple
import logging

from zr.lib.nrf24.mnemonic import *


logger = logging.getLogger(__name__)


Bit = namedtuple('Bit', ('bit', 'len', 'default', 'rw'))


def _BV(x):
    return 1 << x


class Register:
    name = None
    address = None
    _DATA = 0b00
    _BITS = None

    def __init__(self, registry):
        self._registry = registry
        self._radio = registry._radio

        for name, bit in self._BITS.copy().items():
            if isinstance(bit, int):
                self._BITS[name] = Bit(bit, 1, 0, True)
            elif bit.default != 0:
                self._DATA = self._DATA | (bit.default << bit.bit)

    def __int__(self):
        return self._DATA

    def __str__(self):
        s = '{}\n'.format(bin(int(self)))
        for name in sorted(self._BITS):
            s += '{}: {}\n'.format(name, self[name])
        return s

    def __getitem__(self, name):
        if name not in self._BITS:
            raise AttributeError(name)

        return self._get_value(self._BITS[name])

    def __setitem__(self, name, value):
        logger.debug('set registry {}/{} = {}'.format(self.name, name, bin(value)))
        if name not in self._BITS:
            raise AttributeError(name)
        else:
            bit = self._BITS[name]

            mask = (2**bit.len - 1) << (bit.bit - bit.len + 1)
            data = (self._DATA & ~mask) | (value << bit.bit - bit.len + 1)

            self._registry[self.name] = data

    def _get_value(self, bit):
        value = (self._DATA >> (bit.bit - bit.len + 1)) & ((1 << bit.len) - 1)
        if bit.len == 1:
            return bool(value)
        else:
            return value


class IntRegister(Register):
    name = None
    address = None
    keys_startswith = ''
    _DATA = 0b00

    def __init__(self, registry):
        self._registry = registry
        self._radio = registry._radio

    def __str__(self):
        return bin(int(self))

    def __getitem__(self, item):
        item = self._prepare_key(item)
        return bool(self._DATA & _BV(item))

    def __setitem__(self, item, value):
        logger.debug('set registry {}/{} = {}'.format(self.name, item, bin(value)))
        item = self._prepare_key(item)

        if value:
            data = self._DATA | _BV(item)
        else:
            data = self._DATA & ~_BV(item)

        self._registry[self.name] = data

    def _prepare_key(self, key):
        if isinstance(key, int):
            return key
        elif (isinstance(key, str)
                and len(key) == len(self.keys_startswith) + 1
                and key.startswith(self.keys_startswith)):
            return int(key[-1])
        else:
            raise KeyError(key)


class CONFIG_R(Register):
    name = 'CONFIG'
    address = 0x00
    _BITS = {
        'MASK_RX_DR': 6,
        'MASK_TX_DS': 5,
        'MASK_MAX_RT': 4,
        'EN_CRC': Bit(3, 1, 1, True),
        'CRCO': 2,
        'PWR_UP': 1,
        'PRIM_RX': 0,
    }

    def _get_value(self, bit):
        if bit == CRCO:
            return (self._DATA & _BV(bit)) + 1
        else:
            return super()._get_value(bit)


class EN_AA_R(IntRegister):
    name = 'EN_AA'
    address = 0x01
    keys_startswith = 'ENAA_P'
    _DATA = 0b00111111


class EN_RXADDR_R(IntRegister):
    name = 'EN_RXADDR'
    address = 0x02
    keys_startswith = 'ERX_P'
    _DATA = 0b00000011


class SETUP_AW_R(Register):
    name = 'SETUP_AW'
    address = 0x03
    _BITS = {
        'AW': Bit(1, 2, 0b11, True),
    }

#     def __int__(self):
#         return self['AW'] + 2


class SETUP_RETR_R(Register):
    name = 'SETUP_RETR'
    address = 0x04
    _BITS = {
        'ARD': Bit(7, 4, 0b0000, True),
        'ARC': Bit(3, 4, 0b0011, True),
    }

#     def _get_value(self, bit):
#         value = super()._get_value(bit)
#         if bit.bit == 7:
#             return value * 250 + 250
#         else:
#             return value


class RF_CH_R(Register):
    name = 'RF_CH'
    address = 0x05
    _BITS = {
        'RF_CH': Bit(6, 6, 2, False),
    }

    def __int__(self):
        return self['RF_CH']

    def _get_value(self, bit):
        return self._DATA


class RF_SETUP_R(Register):
    name = 'RF_SETUP'
    address = 0x06
    _BITS = {
        'PLL_LOCK': 4,
        'RF_DR': Bit(3, 1, 1, True),
        'RF_PWR': Bit(2, 2, 0b11, True),
        'LNA_HCURR': Bit(0, 1, 1, True),
    }


class STATUS_R(Register):
    name = 'STATUS'
    address = 0x07
    _BITS = {
        'RX_DR': 6,
        'TX_DS': 5,
        'MAX_RT': 4,
        'RX_P_NO': Bit(3, 3, 0b111, False),
        'TX_FULL': Bit(0, 1, 0, False),
    }


class OBSERVE_TX_R(Register):
    name = 'OBSERVE_TX'
    address = 0x08
    _BITS = {
        'PLOS_CNT': Bit(7, 4, 0, False),
        'ARC_CNT': Bit(3, 4, 0, False),
    }


class CD_R(Register):
    name = 'CD'
    address = 0x09
    _BITS = {
        'CD': Bit(0, 1, 0, False),
    }

    def __bool__(self):
        return bool(self['CD'])


class FIFO_STATUS_R(Register):
    name = 'FIFO_STATUS'
    address = 0x17
    _BITS = {
        'TX_REUSE': Bit(6, 1, 0, False),
        'TX_FULL': Bit(5, 1, 0, False),
        'TX_EMPTY': Bit(4, 1, 1, False),
        'RX_FULL': Bit(1, 1, 0, False),
        'RX_EMPTY': Bit(0, 1, 1, False),
    }


class DYNPD_R(IntRegister):
    name = 'DYNPD'
    address = 0x1C
    keys_startswith = 'DPL_P'
    _DATA = 0b0


class FEATURE_R(Register):
    name = 'FEATURE'
    address = 0x1D
    _BITS = {
        'EN_DPL': 2,
        'EN_ACK_PAY': 1,
        'EN_DYN_ACK': 0,
    }


class Registry:
    _REGISTERS_CLASSES = [
        CONFIG_R,
        EN_RXADDR_R,
        EN_AA_R,
        SETUP_AW_R,
        SETUP_RETR_R,
        RF_CH_R,
        RF_SETUP_R,
        STATUS_R,
        OBSERVE_TX_R,
        CD_R,
        FIFO_STATUS_R,
        DYNPD_R,
        FEATURE_R,
    ]

    def __init__(self, radio):
        self._radio = radio
        self._REGISTERS = {}

        for register_class in self._REGISTERS_CLASSES:
            self._REGISTERS[register_class.name] = register_class(self)

    def __getitem__(self, name):
        if name in self._REGISTERS:
            register = self._REGISTERS[name]
            register._DATA = self._radio._read_register(register.address)[0]
            return register
        elif name.startswith('RX_ADDR_P'):
            num = int(name[-1])
            return self._radio._read_register(0x0A + num, 5 if num < 2 else 1)
        elif name == 'TX_ADDR':
            return self._radio._read_register(0x10, 5)  # TX_ADDR
        elif name.startswith('RX_PW_P'):
            num = int(name[-1])
            return self._radio._read_register(0x11 + num)[0]
        else:
            raise KeyError(name)

    def __setitem__(self, name, value):
        logger.debug('set registry {} = {}'.format(name, bin(value)))

        if name in self._REGISTERS:
            self._radio._write_register(self[name].address, value)
        elif name.startswith('RX_ADDR_P'):
            num = int(name[-1])
            return self._radio._write_register(0x0A + num, value, 5 if num < 2 else 1)
        elif name == 'TX_ADDR':
            return self._radio._write_register(0x10, value, 5)  # TX_ADDR
        elif name.startswith('RX_PW_P'):
            num = int(name[-1])
            return self._radio._write_register(0x11 + num, value)
        else:
            raise KeyError(name)
