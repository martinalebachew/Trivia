# Trivia - TCP Quiz Game POC [1.0.1-alpha]
# By Martin Alebachew
# CLIENT.PY
# #####

from protocol import *
from typing import Union
import math
import random
import threading
import socket
from time import sleep
import cv2
import pygame
import pygame_menu

# Client constants
SID = "S"  # Server representation in logs
SCREEN_SIZE = (1080, 720)  # [DO NOT ALTER] Screen dimensions


# GUI static functions
def line_length(pos1, pos2) -> float:
    """
    Returns the distance between the points (pos1) and (pos2).

    :param pos1: (x1, y1)
    :param pos2: (x2, y2)
    :type pos1: (int, int)
    :type pos2: (int, int)
    """
    x1, y1 = pos1
    x2, y2 = pos2
    x_squared = (x2 - x1) * (x2 - x1)
    y_squared = (y2 - y1) * (y2 - y1)
    length = math.sqrt(x_squared + y_squared)
    return length


def click_in_bounds(pos) -> Union[str, None]:
    """
    Hard-coded function to detect click in topic screen.
    Returns topic name or None if pos not in any topic's bounds.

    :param pos: (x, y)
    :type pos: (int, int)
    """

    # Check click Y value for probable topic click
    if 170 < pos[1] < 396 or 436 < pos[1] < 662:

        # Find the closest circle center and check if click is in circle (radius comparison)
        centers = [(239, 270), (540, 270), (841, 270), (239, 536), (540, 536), (841, 536)]
        min_v = int(line_length(centers[0], pos))
        min_i = 0

        for i in range(1, 6):
            d = int(line_length(centers[i], pos))
            if d < min_v:
                min_v = d
                min_i = i

        if min_v <= 100:  # 100 is the topic circle radius
            return TOPICS[min_i]

        # Check rect click
        elif 166 < pos[0] < 313:  # Rects 0, 3
            if pos[1] > 607:  # Rect 3
                return TOPICS[3]
            elif pos[1] > 344:  # Rect 0
                return TOPICS[0]
        elif 467 < pos[0] < 613:  # Rects 1, 4
            if pos[1] > 607:  # Rect 4
                return TOPICS[4]
            elif pos[1] > 344:  # Rect 1
                return TOPICS[1]
        elif 767 < pos[0] < 914:  # Rects 2, 5
            if pos[1] > 607:  # Rect 5
                return TOPICS[5]
            elif pos[1] > 344:  # Rect 2
                return TOPICS[2]


def chosen_answer(pos) -> Union[int, None]:
    """
    Returns the number of the clicked answer (1-4) or None if
    click isn't in any answer's bounds.

    :param pos: (x, y)
    :type pos: (int, int)
    """
    x, y = pos

    if 413 < y < 491:  # Ans 1, 2
        if 72 < x < 505:  # Ans 2
            return 2
        elif 575 < x < 1008:  # Ans 1
            return 1
    elif 528 < y < 606:  # Ans 3, 4
        if 72 < x < 505:  # Ans 4
            return 4
        elif 575 < x < 1008:  # Ans 3
            return 3


def establish_connection(name, ip="127.0.0.1", port=PORT) -> socket.socket:
    """
    Connects to the server and returns a socket.

    :param name: client nickname
    :param ip: server IP address
    :param port: server port
    :type name: str
    :type ip: str
    :type port: int
    """

    s = socket.socket()

    try:
        s.connect((ip, port))
        msg = build_message("I", name)
        send_message(s, SID, msg)
        rsp = recv_message(s, SID)
        if rsp.code != "W":
            raise Error.Client.UnexpectedResponse

    except socket.error as e:
        log(SID, "Error: {}".format(e))
        raise Error.Client.ConnectionFailed

    return s


def random_name() -> str:
    """
    Returns a random nickname.
    """

    names = ["SnowWhite", "Freckles", "Amour", "BettyBoop", "Amorcita", "Chickie", "GreenGiant", "HoneyLocks", "Huggie",
             "Kirby", "Rosebud", "Fellow", "Cheerio", "Dracula", "FrauFrau", "IceQueen", "Ginger", "Smarty", "Fifi",
             "SillyGilly", "Turkey", "BooBear", "Itchy", "Mustache", "Dearey", "Dummy", "Dud", "Ghoulie", "FoxyLady",
             "Butterbuns", "Numbers", "Anvil", "Bubblegum", "Chef", "Doofus", "DillyDally", "Thor", "Beautiful",
             "Donuts", "Loosetooth", "Buds", "Punk", "Snoopy", "Goblin", "Cheddar", "Coach", "CindyLouWho", "LilMama",
             "Junior", "Salt", "HerpDerp", "Backbone", "Wilma", "Flower", "ShortShorts", "Buddy", "CuddlePig",
             "HotPepper", "CutiePie", "Sassy", "DumDum", "Tater", "Buffalo", "Rockette", "Hulk", "Champ", "Juicy",
             "HotSauce", "Buzz", "Tomcat", "Rosie", "CokeZero", "Bruiser", "ToughGuy", "BigNasty", "Chica", "Cricket",
             "Captain", "Heisenberg", "Snickers", "Happy", "Dragonfly", "GummyPop", "Belch", "Papito", "Bug", "Angel",
             "Skipper", "Lobster", "Chum", "Snake", "Kitty", "Focker", "Senorita", "Dolly", "SleepingBeauty", "Cat",
             "Spud", "Grease", "Pickle"]

    return names[random.randint(0, len(names) - 1)]  # Return a random name from the list above


class Gui:
    """ GUI Manager Class """
    def __init__(self):
        # Initialize class variables:
        self.video = None  # [Video Functionality] Video object for mainloop
        self.fps = None  # [Video Functionality] Goal fps variable for mainloop
        self.clock = None  # [Video Functionality] Clock variable for mainloop
        self.fc = None  # [Video Functionality] Frames count variable for mainloop
        self.fm = None  # [Video Functionality] Goal fps variable for mainloop
        self.playvid = False  # [Video Functionality] False if there's no video to play, or the video's path
        self.play_on_vid = {}  # [Video Functionality] Video overlay items

        self.qrsp = None  # [Question Fetching] Temporary question response variable
        self.qc = 0  # [Question Fetching] Question count variable
        self.against = None  # [Question Fetching] Rival nickname variable

        self.sock = None
        self.name = random_name()
        self.ip = "127.0.0.1"

        self.screen = pygame.display.set_mode(SCREEN_SIZE)  # [Mainloop] Pygame screen
        self.state = "welcome"  # [Mainloop] Program's logic variable - current state tracker

        # Initialize GUI:
        #   Application settings:
        print("Initializing...")
        pygame.init()
        pygame.display.set_caption("Play Trivia!")
        icon = pygame.image.load("assets/pictures/icon.png")
        pygame.display.set_icon(icon)

        #   Settings menu
        print("Loading menu...")
        menu = pygame_menu.Menu('Trivia Settings', 400, 300,
                                theme=pygame_menu.themes.THEME_BLUE)

        menu.add.text_input('Name: ', default=self.name, onchange=self.set_name)
        menu.add.text_input('IP: ', default='127.0.0.1', onchange=self.set_ip)
        menu.add.button('Play', self.load_welcome)

        print("Loaded. Waiting for user...")

        menu.mainloop(self.screen)

    def set_name(self, name) -> None:
        """
        pygame-menu method for updating the name variable
        using the name field.
        """

        self.name = name

    def set_ip(self, addr) -> None:
        """
        pygame-menu method for updating the ip variable
        using the ip field.
        """

        self.ip = addr

    def conn_f(self, sock, msg) -> None:
        """
        Thread target function to request a match and update the displayed counter.

        :param sock: connected socket
        :param msg: message string
        :type sock: socket.socket
        :type msg: str
        """

        retry = True

        while retry:
            send_message(sock, SID, msg)
            rsp = recv_message(sock, SID, 2*TIMEOUT)
            # TODO: FIX TIMEOUT
            # TODO: STUCK IN RECV

            if rsp.code == "Q":
                retry = False
                self.qrsp = rsp
                self.against = rsp.fields[5]
                self.state = "question_flag"  # Flag main thread to load a question

            elif rsp.code == "N":
                wait = int(rsp.fields[0])
                font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
                text = font.render(f"{wait}...", True, (255, 255, 255))
                self.play_on_vid["match_seconds_counter"] = (text, (10, 670))

                while wait > 0:
                    sleep(1)
                    wait -= 1
                    font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
                    text = font.render(f"{wait}...", True, (255, 255, 255))
                    self.play_on_vid["match_seconds_counter"] = (text, (10, 670))

                sleep(1)

            else:
                retry = False
                print(f"Client expected \"Q\" or \"N\" message from server,"
                      f"instead got \"{rsp.code}\" response. Loading error screen...")
                sock.close()
                self.raise_error()

    def raise_error(self) -> None:
        """
        Loads error screen.
        """

        self.state = "error"
        self.load_video("assets/videos/error.mp4")

    def close_client(self) -> None:
        """
        Properly exit client
        """

        self.sock.close()
        pygame.quit()
        quit()

    def load_video(self, path, clear=True) -> None:
        """
        Plays a video from a given file path.

        :param path: video file path
        :param clear: clear on-screen elements? (Default=True)
        :type path: str
        :type clear: bool
        """

        if clear:
            self.play_on_vid = {}

        self.playvid = path
        self.video = cv2.VideoCapture(self.playvid)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.fm = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        self.clock = pygame.time.Clock()
        self.fc = 0

    def stop_video(self) -> None:
        """
        Stops the currently playing video.
        If no video is playing - this method has no effect.
        """

        self.playvid = False

    def load_question(self) -> None:
        """
        Load a question from self.qrsp
        """

        self.stop_video()
        print("Loading question screen...")
        sc = pygame.image.load("assets/pictures/question.png")
        self.screen.blit(sc, (0, 0))

        self.qc += 1  # Increment questions counter

        # Load text
        # TODO: FIX HEBREW RTL WORKAROUND
        question_font = pygame.font.Font("assets/fonts/Ploni/Demibold.ttf", 55)
        answers_font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
        header_font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 55)
        large_header_font = pygame.font.Font("assets/fonts/Ploni/Demibold.ttf", 100)

        text = header_font.render(self.against + "משחק נגד "[::-1], True, (255, 255, 255))
        text_rect = text.get_rect()
        self.screen.blit(text, (1080-69-text_rect.width, 60))

        text = header_font.render(f"{self.qc}/{GL}", True, (255, 255, 255))
        self.screen.blit(text, (69, 60))

        text = large_header_font.render(f"שאלה {self.qc}"[::-1], True, (255, 255, 255))
        text_rect = text.get_rect()
        self.screen.blit(text, (1080-69-text_rect.width, 120))

        text = question_font.render(self.qrsp.fields[0][::-1], True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_SIZE[0] / 2, 340))
        self.screen.blit(text, text_rect)

        text = answers_font.render(self.qrsp.fields[1][::-1], True, (255, 255, 255))
        text_rect = text.get_rect(center=(792, 452))
        self.screen.blit(text, text_rect)

        text = answers_font.render(self.qrsp.fields[2][::-1], True, (255, 255, 255))
        text_rect = text.get_rect(center=(289, 452))
        self.screen.blit(text, text_rect)

        text = answers_font.render(self.qrsp.fields[3][::-1], True, (255, 255, 255))
        text_rect = text.get_rect(center=(792, 567))
        self.screen.blit(text, text_rect)

        text = answers_font.render(self.qrsp.fields[4][::-1], True, (255, 255, 255))
        text_rect = text.get_rect(center=(289, 567))
        self.screen.blit(text, text_rect)

        self.state = "question"
        print("Loaded. Waiting for user...")

    def load_welcome(self) -> None:
        """
        Load welcome screen.
        """

        #   Welcome screen:
        print("Loading welcome screen...")
        welcome_bg = pygame.image.load("assets/pictures/welcome.png")
        self.screen.blit(welcome_bg, (0, 0))

        #   Load credit text:
        font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 32)
        text = font.render("מרטין אלבצאו"[::-1], True, (255, 255, 255))  # Reverse string as a workaround for RTL bug
        self.screen.blit(text, (900, 680))

        print("Loaded. Waiting for user...")
        self.run()
        # TODO: do not call run method

    def load_topics_screen(self) -> None:
        """
        Load topics screen.
        """

        print("Loading topics screen...")
        sc = pygame.image.load("assets/pictures/topics.png")
        self.screen.blit(sc, (0, 0))
        self.state = "topics"
        print("Loaded. Waiting for user...")

    def handle_mouse_click_on_topic(self) -> None:
        topic = click_in_bounds(pygame.mouse.get_pos())

        if topic:
            print(f"Loading match screen for topic {topic}...")
            self.state = "match"
            self.load_video("assets/videos/match.mp4")
            print("Loaded. Connecting to server...")

            self.sock = establish_connection(self.name, ip=self.ip)
            msg = build_message("S", topic)
            print("Connection established. Requesting match...")

            # Start another thread to handle connection and update counter
            conn_t = threading.Thread(target=self.conn_f, args=(self.sock, msg))
            conn_t.start()

    def load_next_question(self) -> None:
        """
        Loads next question / game results.
        """

        # wait for the next question
        rsp = recv_message(self.sock, SID, timeout=TIMEOUT + ANS)
        # TODO: FIX TIMEOUT

        if rsp.code == "Q":
            # Load question screen
            self.qrsp = rsp
            self.load_question()

        elif rsp.code == "R":
            # Load results screen
            print("Loading results screen...")

            if rsp.fields[0] == self.name:
                bg = pygame.image.load("assets/pictures/winner.png")
                self.state = "winner"

            elif rsp.fields[0] == "B":
                bg = pygame.image.load("assets/pictures/tie.png")
                self.state = "tie"

            else:
                bg = pygame.image.load("assets/pictures/loser.png")
                self.state = "loser"

            self.screen.blit(bg, (0, 0))
            print("Loaded. Waiting for user...")

        else:
            print(f"Client expected \"Q\" or \"R\" message from server,"
                  f"instead got \"{rsp.code}\" response. Loading error screen...")
            self.raise_error()

    def playvid_mainloop(self) -> None:
        """
        Handle video playing in the mainloop - one frame at a time.
        """

        if self.fc == self.fm:
            self.video = cv2.VideoCapture(self.playvid)
            self.fc = 0

        self.clock.tick(self.fps)

        success, video_image = self.video.read()
        video_surf = None

        if success:
            video_surf = pygame.image.frombuffer(
                video_image.tobytes(), video_image.shape[1::-1], "BGR")

        self.screen.blit(video_surf, (0, 0))
        self.fc += 1

        for p in self.play_on_vid.items():
            self.screen.blit(p[1][0], p[1][1])

    def run(self) -> None:
        """ Mainloop function """

        while True:
            # Handle video playing:
            if self.playvid:
                self.playvid_mainloop()

            # Handle thread flags:
            if self.state == "question_flag":
                self.load_question()
                self.state = "question"

            # Handle events:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close_client()

                elif event.type == pygame.MOUSEBUTTONDOWN and self.state != "error":
                    if event.button == 1:
                        if self.state == "welcome":
                            self.load_topics_screen()

                        elif self.state == "topics":
                            self.handle_mouse_click_on_topic()

                        elif self.state == "question":
                            ans = chosen_answer(pygame.mouse.get_pos())  # Calculate chosen answer

                            if ans:
                                send_message(self.sock, SID, build_message("A", ans))  # Send answer to server
                                self.load_next_question()  # Load next question / game results

            pygame.display.flip()  # Update screen


def main():
    Gui()


if __name__ == "__main__":
    main()