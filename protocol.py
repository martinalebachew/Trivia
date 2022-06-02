# Trivia - TCP Quiz Game POC [1.0.1-alpha]
# By Martin Alebachew
# PROTOCOL.PY
# #####

# Protocol-wide settings
PORT = 15999  # Protocol port
TIMEOUT = 3  # Default recv timeout (seconds)
BUFF = 1024  # recv buffer size

DW = 5  # Time to wait before asking for rematch
ANS = 10  # Time to answer question - before timeout
GL = 3  # Game length

MSG_CODES = ["I", "W", "S", "C", "N", "Q", "A", "R", "E"]  # Existing messages in protocol
TOPICS = ["lit", "art", "sci", "cyb", "mus", "cin"]  # Trivia topics by pos (DO NOT ALTER)


# Protocol-wide classes
class Error:
    class Protocol:
        class UnknownMessageCode(Exception):
            pass

        class MessageValidationError(Exception):
            pass

    class Client(Exception):
        pass

    class Server(Exception):
        pass


# Protocol-wide functions
def log(conn, info) -> None:
    """
    Logs given info to the console.

    :param conn: connection info string
    :param info: desired printed info
    """

    print(f"({conn}) {info}")


def build_message(code, *fields) -> str:
    """
    Builds a message according to protocol.

    :param code: message code
    :param fields: additional fields
    :type code: str
    :type fields: str
    :return: validated message string
    :raises UnknownMessageCode: if message code is not defined in protocol
    """

    if code not in MSG_CODES: raise Error.Protocol.UnknownMessageCode  # Validate message type

    # Add encoded parameters
    msg = code
    for field in fields:
        msg += "~" + str(field)

    # Return validated message
    if break_message(msg) == (code, [str(field) for field in fields]):
        return msg
    raise Error.Protocol.MessageValidationError


def break_message(msg) -> (str, list[str]):
    """
    Break down a message built according to protocol.

    :param msg: message string
    :type msg: str
    :raises UnknownMessageCode: if message code is not defined in protocol
    """

    msg = msg.split("~")
    code = msg.pop(0)
    if code not in MSG_CODES:
        raise Error.Protocol.UnknownMessageCode
    return code, msg


def send_message(sock, conn, msg) -> None:
    """
    Sends an unencoded message to a given socket and logs it.

    :param sock: connected target socket
    :param conn: connection info string
    :param msg: unencoded message string
    :type sock: socket.socket
    :type conn: str
    :type msg: str
    """

    sock.send(msg.encode())
    log(conn, f">>>>> {msg}")


def recv_message(sock, conn, timeout=TIMEOUT) -> (str, list[str]):
    """
    Receives a message from a given socket and logs it.

    :param sock: connected target socket
    :param conn: connection info string
    :param timeout: socket recv timeout
    :type sock: socket.socket
    :type conn: str
    :type timeout: int
    """

    sock.settimeout(timeout)
    msg = sock.recv(BUFF).decode()
    log(conn, f"<<<<< {msg}")
    return break_message(msg)
