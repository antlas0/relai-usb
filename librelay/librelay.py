#!/usr/bin/env python3


import time
import struct
import serial
import inspect
from enum import Enum
from queue import Queue
from threading import Thread
from typing import Optional, List
from serial.tools import list_ports


class APIAction(Enum):
    """
    List of action to specify when dealing with the Queue
    SET_STATE: set the state of the relay
    QUERY: get info from the relay
    """
    UNKNOWN = 0
    SET_STATE = 1
    QUERY = 2


class RelayStates(Enum):
    """
    Values to send to the relay to actually set the state
    """
    ALL_ON  =   100
    ALL_OFF =   110
    ONE_ON  =   101
    ONE_OFF =   111
    TWO_ON  =   102
    TWO_OFF =   112


class RelayQueries(Enum):
    """
    Values to send to the relay to get info
    """
    VERSION =   90
    STATUS  =   91


class LibRelay02(Thread):
    def __init__(self, device:str="/dev/ttyACM0", bauds:int=115200) -> None:
        super().__init__()
        self._device = device
        self._bauds = bauds
        self._running = True
        self._filedesc = None
        self._input_queue = None
        self._output_queue = None
        self._populate_relay_states_apis()

    def input_queue(self) -> Optional[Queue]:
        """
        Gets the input queue
        returns: Optional[Queue]
        """
        return self._input_queue
    
    def set_input_queue(self, q:Queue) -> None:
        """
        Assign a queue for incoming commands
        q: the input queue
        returns: None
        """
        self._input_queue = q

    def output_queue(self) -> Optional[Queue]:
        """
        Gets the output queue
        returns: Optional[Queue]
        """
        return self._output_queue

    def set_output_queue(self, q:Queue) -> None:
        """
        Assign a queue for outgoing messages
        q: the output queue
        returns: None
        """
        self._output_queue = q

    def setup(self) -> bool:
        """
        Setups the class, open the serial port
        with the configuration
        returns: True on success, else False
        """
        try:
            self._filedesc = serial.Serial(
                self._device,
                self._bauds,
                parity=serial.PARITY_NONE,
                bytesize=8,
                stopbits=1
                )
        except Exception as e:
            print(str(e))
            return False
        else:
            return True
        finally:
            pass

    def __clear_queue(self, q:Queue) -> None:
        """
        Utility to clear a queue
        returns: None
        """
        while not q.empty():
            try:
                q.get(block=False)
            except Exception as e:
                logger.warning(str(e))
                continue
            q.task_done()

    def quit(self) -> None:
        """
        Close the file descriptor
        returns: None
        """
        self._running = False
        self.__clear_queue(self._input_queue)
        self._filedesc.close()

    def version(self) -> bytes:
        """
        Ask the system its version through the serial port
        returns: bytes
        """
        to_write = struct.pack('!B', RelayQueries.VERSION.value)
        self._filedesc.write(to_write)
        time.sleep(0.1)
        res = self._filedesc.read(size=2)
        return res

    def status(self) -> bytes:
        """
        Ask the system each contacteur states
        returns: bytes
        """
        to_write = struct.pack('!B', RelayQueries.STATUS.value)
        self._filedesc.write(to_write)
        time.sleep(0.1)
        res = self._filedesc.read(size=1)
        return res

    def _populate_relay_states_apis(self) -> None:
        """
        Create methods that will be assignated to the current class,
        based on the RelayStates and RelayQueries classes
        returns: None
        """
        def __make_command_fct(instance, name, value):
            def tmp_fct() -> bytes:
                to_write = struct.pack('!B', value)
                res = instance._filedesc.write(to_write)
                time.sleep(0.1)
                return res
            tmp_fct.__name__ = name
            tmp_fct.__qualname__ = name
            tmp_fct.__doc__ = name
            return tmp_fct

        instance = self
        for member in RelayStates:
            f = __make_command_fct(instance, member.name.lower(), member.value)
            setattr(instance, member.name.lower(), f)

    def _analyse(self, command:dict) -> Optional[bytes]:
        """
        Analyse commands and send them to the relay

        Format is a dictionnary

        Example :
        { "action": APIAction.SET_STATE.name, "content": RelayStates.ALL_ON.name }
        { "action": APIAction.QUERY.name, "content": RelayQueries.VERSION.name }

        returns: bytes from the serial response
        """
        if not "action" in command:
            return

        if not APIAction.SET_STATE.name in command["action"] and not APIAction.QUERY.name in command["action"]:
            return

        try:
            res = getattr(self, command["content"].lower())()
        except Exception as e:
            print(str(e))
            return
        else:
            return res


    def run(self) -> None:
        """
        The threading callback, loops on the input queue
        for incoming commands
        returns: None
        """
        while self._running:
            command = self._input_queue.get()
            res = self._analyse(command)
            self._output_queue.put(res)
