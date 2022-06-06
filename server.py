# Trivia - TCP Quiz Game POC [1.1.0-alpha]
# By Martin Alebachew
# SERVER.PY
# #####

from protocol import *
from typing import Union
import random
import socket
import threading
from time import sleep

# Server global variable
waitlist = {k: [] for k in TOPICS}  # Waiting list by topic dict - see server documentation
score = {}  # Score dict - see server documentation
questions = {}  # [THREAD READONLY] questions by topic dict - see server documentation
lock = threading.Lock()  # Lock for accessing global vars above


# Server classes
class Client:
    def __init__(self, name, sock, addr, cid, thread=None):
        """
        Represents a typical client.

        :param name: nickname string chosen by the client, passed in 'I' message.
        :param sock: connected client socket
        :param addr: client address tuple
        :param cid: client id
        :param thread: client-handling stoppable thread
        :type name: str
        :type sock: socket.socket
        :type addr: (str, int)
        :type cid: str
        :type thread: ServerThread
        """

        self.name = name
        self.sock = sock
        self.addr = addr
        self.cid = cid
        self.thread = thread


class ServerThread(StoppableThread):
    def __init__(self, sock, addr, cid):
        """
        Client-handling thread.

        :param sock: connected client socket
        :param addr: client address tuple
        :param cid: client id
        :type sock: socket.socket
        :type addr: (str, int)
        :type cid: str
        """

        self.sock = sock
        self.addr = addr
        self.cid = cid
        super().__init__(self.handle_client)  # Initialize a Stoppable Thread with handle_client as target function

    def handle_client(self) -> None:
        """
        Client-handling logic.
        """

        log(self.cid, f"New connection from {self.addr}")
        msg = recv_message(self.sock, self.cid)  # Get 'I' authentication message

        if msg.code == "I":
            name = msg.fields[0]
            send_message(self.sock, self.cid, build_message("W"))  # Send welcome message

            msg = recv_message(self.sock, self.cid)  # Get 'S' message (search for game)
            topic = None

            while msg.code == "S":
                client = Client(name, self.sock, self.addr, self.cid, self)
                match = match_clients(msg.fields[0], client)
                topic = msg.fields[0]  # Save the topic which contains client in the waiting list

                if not match:
                    msg = None
                    while not msg:
                        if self.stopped():
                            """
                            Because one of the threads removes the other client from the waiting list,
                            and only one thread can access it at a time,
                            one of them is bound to stop the other while it's still searching a match,
                            specifically waiting for a S/C query from the client.
                            """

                            log(self.cid, f"Game found, but managed by another thread. Closing thread.")
                            return

                        msg = recv_message(self.sock, self.cid, timeout=0.1)

                else:
                    manage_game(msg.fields[0], client, match)
                    break

            else:
                if msg.code == "C":
                    log(self.cid, f"Client canceled game. Closing connection.")

                    if topic:  # Remove client from waiting list
                        with lock:
                            for i in range(0, len(waitlist[topic])):
                                c = waitlist[topic][i]

                                if c.addr == self.addr:
                                    waitlist[topic].pop(i)

                    self.sock.close()

                else:
                    log(self.cid, f"Expected \"S\" query, instead got \"{msg.code}\". Closing connection.")
                    self.sock.close()

        else:
            log(self.cid, f"Expected \"I\" query, instead got \"{msg.code}\". Closing connection.")
            self.sock.close()


# Server static functions
def recv_f(tid, target, correct) -> None:
    """
    Simple target function to get answer from user and add score accordingly.

    :param tid: thread id (key in score dict)
    :param target: target client
    :param correct: correct answer
    :type tid: str
    :type target: Client
    :type correct: int
    """

    msg = recv_message(target.sock, target.cid, timeout=TIMEOUT + ANS)  # TODO: FIX TIMEOUT
    if int(msg.fields[0]) == correct:
        with lock:
            score[tid][target.cid] += 1  # TODO: TIME-BASED SCORE


def add_to_waitlist(topic, client) -> None:
    """
    Add a client to the waiting list of a given topic.
    ADD LOCK MANUALLY

    :param topic: chosen topic
    :param client: client to add
    :type topic: str
    :type client: Client
    """

    if topic not in TOPICS or topic not in waitlist.keys():
        raise Error.Protocol.UnknownTopic

    for i in range(0, len(waitlist[topic])):  # Make sure there isn't any inactive connection from same address
        match = waitlist[topic][i]
        if match.addr == client.addr:
            waitlist[topic].pop(i)

    if client not in waitlist[topic]:
        waitlist[topic].append(client)


def get_from_waitlist(topic, client) -> Union[Client, None]:
    """
    Returns a client from waitlist of a given topic (FIFO),
    or None if no matching client was found.
    ADD LOCK MANUALLY

    :param topic: given topic
    :param client: current client
    :type topic: str
    :type client: Client
    """

    if topic not in TOPICS or topic not in waitlist.keys():
        raise Error.Protocol.UnknownTopic

    for i in range(0, len(waitlist[topic])):
        if waitlist[topic][i].addr != client.addr:  # if matching client is not the same as the current client
            match = waitlist[topic].pop(i)  # pop from list
            if client in waitlist[topic]:  # remove current client from waitlist
                waitlist[topic].remove(client)
            return match


def question_set(topic, length) -> set[Question]:
    """
    Returns a random set of questions in given topic and in given length.

    :param topic: chosen topic, as defined in the protocol
    :param length: number of questions to generate
    :raises Error.Protocol.UnknownTopic: if the requested topic is not defined in the protocol or not
    found in the questions file
    :raises Error.Server.NotEnoughQuestions: if the requested length is greater than the number
    of questions available in that topic
    """

    if topic not in TOPICS or topic not in questions.keys():
        raise Error.Protocol.UnknownTopic

    if len(questions[topic]) < length:
        raise Error.Server.NotEnoughQuestions
    elif len(questions[topic]) == length:
        return set(questions[topic])
    else:
        available_q = list(questions[topic])  # NEW Temporary list of existing questions in the given topic
        questions_set = set()

        for i in range(0, length):
            j = random.randint(0, len(available_q) - 1)  # pick a random not chosen question
            questions_set.add(available_q[j])  # add to set
            available_q.pop(j)  # remove question from list of not chosen questions
        return questions_set


def match_clients(topic, client) -> Union[Client, None]:
    """
    Searches a match for the current client and returns its client object.
    If a match is not found, adds the client to the waiting list and returns None.

    :param topic: chosen topic
    :param client: current client
    :type topic: str
    :type client: Client
    """
    with lock:
        match = get_from_waitlist(topic, client)

        if not match:  # if match is not found
            # add to waiting list send 'N' message with time to wait before retrying
            add_to_waitlist(topic, client)
            log(client.cid, "Added to waitlist")
            send_message(client.sock, client.cid, build_message("N", DW))
        else:
            # stop other thread and return the other client object
            match.thread.stop()
            return match


def manage_game(topic, client, match) -> None:
    """
    In-game logic.

    :param client: main client
    :param match: second client
    :param topic: game topic
    :type client: Client
    :type match: Client
    :type topic: str
    """

    tid = client.cid  # Thread id and score key

    # New client ids
    client.cid = str(tid) + "-1"
    match.cid = str(tid) + "-2"

    # Initialize score dict for the current game
    with lock:
        score[tid] = {
            client.cid: 0,
            match.cid: 0
        }

    game_questions = question_set(topic, GL)  # get a random set of questions

    prev_ans = None
    for i in range(0, len(game_questions)):
        q = game_questions.pop()
        q.randomize()  # Randomize answers for the question

        if i == 0:  # for the first question - send with the nickname of client's rival
            send_message(client.sock, client.cid, build_message("Q", q.q, q.a1, q.a2, q.a3, q.a4, match.name))
            send_message(match.sock, match.cid, build_message("Q", q.q, q.a1, q.a2, q.a3, q.a4, client.name))
        else:  # for the rest - send with the answer of the previous question
            msg = build_message("Q", q.q, q.a1, q.a2, q.a3, q.a4, prev_ans)
            send_message(client.sock, client.cid, msg)
            send_message(match.sock, match.cid, msg)

        prev_ans = q.c

        # get answer from both clients at the same time using threads
        t1 = threading.Thread(target=recv_f, args=(tid, client, q.c))
        t2 = threading.Thread(target=recv_f, args=(tid, match, q.c))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        sleep(0.2)  # Slight delay between questions

    # calculate and send game results to both clients
    if score[tid][client.cid] > score[tid][match.cid]:
        msg = build_message("R", client.name, prev_ans)
    elif score[tid][client.cid] < score[tid][match.cid]:
        msg = build_message("R", match.name, prev_ans)
    else:
        msg = build_message("R", "B", prev_ans)

    send_message(client.sock, client.cid, msg)
    send_message(match.sock, match.cid, msg)

    # close client sockets
    log(tid, f"Game ended. Closing sockets and exiting thread.")
    client.sock.close()
    match.sock.close()


def main():
    global questions
    questions = load_questions()

    # Create and bind the server main socket
    ss = socket.socket()
    ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ss.bind(("0.0.0.0", PORT))
    ss.listen()

    print("Server is online.")

    cid = 1  # Client id counter
    while True:
        cs, ca = ss.accept()
        ServerThread(cs, ca, str(cid)).start()  # Launch client-handling thread
        cid += 1


if __name__ == "__main__":
    main()
