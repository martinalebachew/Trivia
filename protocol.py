# Trivia - TCP Quiz Game POC [2.0.0]
# By Martin Alebachew
# PROTOCOL.PY
# #####

import socket
import threading
from random import randint

# Protocol-wide settings
PORT = 15999  # Protocol port
TIMEOUT = 3  # Default recv timeout (seconds)
BUFF = 1024  # recv buffer size

DW = 5  # Time to wait before asking for rematch
ANS = 10  # Time to answer question - before timeout
GL = 8  # Game length

MSG_CODES = ["I", "W", "S", "C", "N", "Q", "A", "R", "E"]  # Existing messages in protocol
TOPICS = ["lit", "art", "sci", "mix", "mus", "cin"]  # Trivia topics by pos (DO NOT ALTER)


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

    def randomize(self):
        """
        Randomize order of answers.
        """
        new_c = randint(1, 4)

        # Using exec to swap old and new position of correct answer
        exec(f"self.a{new_c}, self.a{self.c} = self.a{self.c}, self.a{new_c}")
        self.c = new_c


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


class StoppableThread(threading.Thread):
    def __init__(self, target):
        """
        Thread class with a stop() method. The target function has to
        check regularly for the stopped() condition.

        :param target: target function
        :type target: function
        """

        super().__init__(target=target)  # Initialize a threading.Thread object with passed target function
        self._stop_event = threading.Event()  # Create a stop flag event

    def stop(self) -> None:
        """
        Raise stop flag for the thread.
        """

        self._stop_event.set()

    def stopped(self) -> bool:
        """
        Check if stop flag has been raised.

        :return: True if it has been raised, False otherwise.
        """

        return self._stop_event.is_set()


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

    if msg == "":
        return None

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


def recv_message(sock, conn, timeout=TIMEOUT):
    """
    Receives a message from a given socket and logs it.

    :param sock: connected target socket
    :param conn: connection info string
    :param timeout: socket recv timeout
    :type sock: socket.socket
    :type conn: str
    :type timeout: Union[float, int]
    """

    sock.settimeout(timeout)
    try:
        msg = sock.recv(BUFF).decode()
    except TimeoutError:
        return None

    log(conn, f"<<<<< {msg}")
    return break_message(msg)


def load_questions() -> dict[str, list[Question]]:
    """
    Loads all questions from ./questions directory
    and returns a dict of questions by topic.
    """

    questions = {topic: [] for topic in TOPICS}

    for topic in TOPICS:
        if topic != "mix":
            with open(f"questions/{topic}.txt", "r") as f:
                topic_questions = f.read().split("\n\n")
                for q in topic_questions:
                    q = q.split('\n')
                    questions[topic].append(Question(q[0], q[1], q[2], q[3], q[4], 1))
                    questions["mix"].append(Question(q[0], q[1], q[2], q[3], q[4], 1))

    return questions
