## Librelay
### Description
This library is meant to control the USB-RLY02 product from Devantech, using its serial communication.
### Installation
Create a virutal environment and install the dependencies.
```bash
$ python3 -m venv .venv 
$ source ./venv/bin/activate

# verify
$ which python3

$ python3 -m pip install -r requirements.txt
```

Use the `setup.py` to install as a development
```bash
$ python3 setup.py develop
```

### How to use
#### Unthreaded APIs
Set up the arguments
```python
args = {
    "device": "/dev/ttyACM0",
    "bauds": 115200,
}
```
Instanciate the class.
```python
lr = LibRelay02(args["device"], int(args["bauds"]))
```

If `setup` the instance succeed, you can directly call the unthreaded APIs

```python
if lr.setup():
    print(f"[I]: Version {lr.version()}")
    print(f"[I]: Version {lr.status()}")
    lr.all_on()
    lr.all_off()
    lr.one_on()
    lr.one_off()
    lr.two_on()
    lr.two_off()
```

#### Threaded APIs
We use `Queue`s to send commands to the class and retrieve the responses from the serial communication.
The command format is the following :
* A dictionnary with the fields "action" and "query".

```python
class APIAction(Enum):
    """
    List of action to specify when dealing with the Queue
    SET_STATE: set the state of the relay
    QUERY: get info from the relay
    """
    UNKNOWN = 0
    SET_STATE = 1
    QUERY = 2
```

An action is to either set the contactor states or query information.
```bash
    { "action": APIAction.SET_STATE.name, "content": RelayStates.ALL_ON.name }
    { "action": APIAction.QUERY.name, "content": RelayQueries.VERSION.name }
```
Here are the `enum` forthe queries : a relay state or information query.
```python
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
```

Here is an example :
```python
lr = LibRelay02(args["device"], int(args["bauds"]))
q, r = Queue(), Queue()
if lr.setup():
    lr.set_input_queue(q)
    lr.set_output_queue(r)
    lr.start()
    q.put({"action": APIAction.QUERY.name, "content": RelayQueries.VERSION.name})
    print(r.get())
    q.put({"action": APIAction.SET_STATE.name, "content": RelayStates.ALL_ON.name})
    print(r.get())
```

### Uninstall

Just use `pip`.
```bash
$ python3 -m pip uninstall librelay
```

---