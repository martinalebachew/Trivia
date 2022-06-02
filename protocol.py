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

        class UnknownTopic(Exception):
            pass

        class MessageValidationError(Exception):
            pass

    class Client:
        class ConnectionFailed(Exception):
            pass

        class UnexpectedResponse(Exception):
            pass

    class Server:
        class InvalidArgs(Exception):
            pass

        class NotEnoughQuestions(Exception):
            pass


class Question:
    def __init__(self, q, a1, a2, a3, a4, c):
        """
        Represents a question, its available answers and chosen answer.

        :param q: question string
        :param a1: first answer
        :param a2: second answer
        :param a3: third answer
        :param a4: fourth answer
        :param c: correct answer number (1-4)
        :type q: str
        :type a1: str
        :type a2: str
        :type a3: str
        :type a4: str
        :type c: int
        """

        self.q = q
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        self.c = c


class Message:
    def __init__(self, code, fields=None):
        """
        Represents a single message of any code, according to protocol.

        :param code: message code
        :param fields: additional fields
        :type code: str
        :type fields: list[str]
        """

        self.code = code
        self.fields = fields

    def __eq__(self, other):
        if not isinstance(other, Message):
            return NotImplemented

        if len(self.fields) != len(other.fields) or self.code != other.code:
            return False

        for i in range(0, len(self.fields)):
            if self.fields[i] != other.fields[i]:
                return False

        return True


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
    :type fields: Union[str, int]
    :return: validated message string
    :raises UnknownMessageCode: if message code is not defined in protocol
    """

    if code not in MSG_CODES: raise Error.Protocol.UnknownMessageCode  # Validate message type

    # Add encoded parameters
    msg = code
    for field in fields:
        msg += "~" + str(field)

    # Return validated message
    if break_message(msg) == Message(code, [str(field) for field in fields]):
        return msg
    raise Error.Protocol.MessageValidationError


def break_message(msg) -> (str, list[str]):
    """
    Break down a message built according to protocol.

    :param msg: message string
    :type msg: str
    :raises UnknownMessageCode: if message code is not defined in protocol
    """

    fields = msg.split("~")
    code = fields.pop(0)
    if code not in MSG_CODES:
        raise Error.Protocol.UnknownMessageCode
    return Message(code, fields)


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


def main():
    x = build_message("I", "galwhawhy")


if __name__ == "__main__":
    main()
