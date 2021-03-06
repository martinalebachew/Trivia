# Trivia - TCP Quiz Game POC [2.0.0]
# By Martin Alebachew
# CLIENT.PY
# #####

from protocol import *
from typing import Union
import math
import random
import socket
from time import sleep
import cv2
import pygame
from string import ascii_letters

# Client constants
SID = "S"  # Server representation in logs
SCREEN_SIZE = (1080, 720)  # [DO NOT ALTER] Screen dimensions
ANS_CENT = [(792, 452), (289, 452), (792, 567), (289, 567)]
HEB_CHARS = "אבגדהוזחטיכלמנסעפצקרשתץןםףך"
CONT_SEQ = " ־–-:״\"',׳()"


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


def hebrew_proof(text) -> str:
    """
    Returns a reformatted string for pygame to view in hebrew.
    KNOWN BUG with leading AND trailing cont_chars around non-hebrew text.

    :param text: text to reformat
    :type text: str
    """

    spl = []
    ts = ""
    heb_seq = False
    heb_dec = False

    for ch in text:
        if ch in HEB_CHARS or (ch in CONT_SEQ and heb_seq):  # if in hebrew
            if not heb_seq:  # if prev seq not in hebrew
                spl.append(ts)  # save not reversed
                ts = ""

            heb_seq = True
            heb_dec = True  # hebrew somewhere in text
            ts += ch

        else:  # if not in hebrew
            if heb_seq:  # if prev seq in hebrew
                spl.append(ts[::-1])  # save reversed
                ts = ""

            heb_seq = False
            ts += ch

    if ts != "":  # save last sequence
        spl.append(ts[:: -1 if heb_seq else 1])

    if heb_dec:  # if there's hebrew in text - reverse order of sequences
        spl.reverse()

    return "".join(spl)


class TextboxMgr:
    def __init__(self, screen, value="", fontsize=20, pos=(0, 0)):
        """
        Represents a textbox on settings page.

        :param screen: main surface
        :param value: default text value
        :param fontsize: inner text font size
        :param pos: position on screen
        :type screen: pygame.Surface
        :type value: str
        :type fontsize: int
        :type pos: (int, int)
        """

        self.screen = screen
        self.value = value
        self.field_color = (61, 65, 118)

        self.font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", fontsize)
        self.input_rect = pygame.Rect(pos[0], pos[1], 416, 58)

    def blit(self):
        # Draw textbox
        pygame.draw.rect(self.screen, self.field_color, self.input_rect, 0)
        text_surface = self.font.render(self.value, True, (255, 255, 255))
        self.screen.blit(text_surface, (self.input_rect.x + 10, self.input_rect.y + 7))

    def highlight(self):
        # Color textbox
        self.field_color = (134, 170, 223)
        self.blit()

    def dehighlight(self):
        # De-color textbox
        self.field_color = (61, 65, 118)
        self.blit()


class MatchThread(StoppableThread):
    def __init__(self, gui, sock, msg):
        self.sock = sock
        self.msg = msg
        self.gui = gui
        super().__init__(self.conn_f)  # Initialize a Stoppable Thread with conn_f as target function

    def conn_f(self) -> None:
        """
        Thread target function to request a match and update the displayed counter.

        :param sock: connected socket
        :param msg: message string
        :type sock: socket.socket
        :type msg: str
        """

        retry = True

        while retry:
            send_message(self.sock, SID, self.msg)
            rsp = recv_message(self.sock, SID, TIMEOUT)

            if rsp.code == "Q":
                retry = False
                self.gui.qrsp = rsp
                self.gui.against = rsp.fields[5]
                self.gui.state = "question_flag"  # Flag main thread to load a question

            elif rsp.code == "N":
                wait = int(rsp.fields[0])
                font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
                text = font.render(f"{wait}...", True, (255, 255, 255))
                self.gui.play_on_vid["match_seconds_counter"] = (text, (10, 670))

                while wait > 0:
                    for i in range(0, 100):
                        sleep(0.01)
                        msg = recv_message(self.sock, SID, 0.001)
                        if msg and msg.code == "Q":
                            self.gui.qrsp = msg
                            self.gui.against = msg.fields[5]
                            self.gui.state = "question_flag"  # Flag main thread to load a question
                            return

                    if self.stopped():
                        send_message(self.sock, SID, build_message("C"))
                        retry = False
                        break
                    else:
                        wait -= 1
                        font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
                        text = font.render(f"{wait}...", True, (255, 255, 255))
                        self.gui.play_on_vid["match_seconds_counter"] = (text, (10, 670))

                sleep(1)

            else:
                retry = False
                print(f"Client expected \"Q\" or \"N\" message from server,"
                      f"instead got \"{rsp.code}\" response. Loading error screen...")
                self.sock.close()
                self.gui.raise_error()


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
        self.qt = ANS  # [Question Fetching] Question timer variable
        self.against = None  # [Question Fetching] Rival nickname variable

        self.sock = None  # [Network] Connection socket
        self.name = random_name()  # [Network] Nickname
        self.ip = "127.0.0.1"  # [Network] Server IP address

        self.conn_t = None  # [Matching] Match searching thread
        self.chosen_ans = False  # [Matching] Flag to avoid double answering

        self.screen = pygame.display.set_mode(SCREEN_SIZE)  # [Mainloop] Pygame screen
        self.state = None  # [Mainloop] Program's logic variable - current state tracker
        self.topic = None  # [Mainloop] Current game topic

        # Initialize GUI:
        #   Application settings:
        print("Initializing...")
        pygame.init()

        self.screen.fill((140, 82, 255))  # BG color behind textbox
        self.namemgr = TextboxMgr(self.screen, self.name, 40, (164, 354))
        self.ipmgr = TextboxMgr(self.screen, self.ip, 40, (164, 433))

        pygame.display.set_caption("Play Trivia!")
        icon = pygame.image.load("assets/pictures/icon.png")
        pygame.display.set_icon(icon)

        self.timer_font = pygame.font.Font("assets/fonts/Ploni/Demibold.ttf", 40)
        self.question_font = pygame.font.Font("assets/fonts/Ploni/Demibold.ttf", 55)
        self.answers_font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
        self.header_font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 55)
        self.large_header_font = pygame.font.Font("assets/fonts/Ploni/Demibold.ttf", 100)

        self.load_welcome_screen()
        pygame.mixer.init()
        pygame.mixer.music.load('assets/sound/theme.mp3')
        pygame.mixer.music.play(-1)  # Play indefinitely
        pygame.mixer.music.pause()
        self.music_paused = True

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
        self.screen.fill((140, 82, 255))
        sc = pygame.image.load("assets/pictures/question.png")
        self.screen.blit(sc, (0, 0))

        self.qc += 1  # Increment questions counter
        self.qt = ANS  # Reset question timer
        self.chosen_ans = False

        # Load text
        self.load_question_text(str(ANS), self.timer_font, center=(971, 183))
        self.load_question_text(hebrew_proof(f"משחק נגד {self.against}"), self.header_font, lambda_f=lambda w, h: (1011-w, 60))
        self.load_question_text(hebrew_proof(f"{self.qc}/{GL}"), self.header_font, pos=(69, 60))
        self.load_question_text(hebrew_proof(f"שאלה {self.qc}"), self.large_header_font, lambda_f=lambda w, h: (915-w, 120))
        self.load_question_text(hebrew_proof(self.qrsp.fields[0]), self.question_font, center=(SCREEN_SIZE[0] / 2, 340))

        for i in range(1, 5):
            self.load_question_text(hebrew_proof(self.qrsp.fields[i]), self.answers_font, center=ANS_CENT[i - 1], bgc=(61, 65, 118))

        self.state = "question"

        # Launch timer thread
        timer_t = threading.Thread(target=self.decrement_question_timer, args=(self.qc,))
        timer_t.start()

        print("Loaded. Waiting for user...")

    def decrement_question_timer(self, qc):
        """
        Decrements the timer until reaches 0,
        then sends a 0 answer to the server.

        -- Workaround to avoid stoppableThread --
        Thread checks the current question number,
        with the original question number,
        and terminates accordingly.

        Also, chosen_answer variable is there
        because during sleep(1),
        when the timer displays '0',
        the user might have clicked on an answer,
        and then we should not send '0' to the server.
        --

        :param qc: Question number
        :type qc: int
        """

        while self.qt > 0:
            if self.qc != qc:
                return

            sleep(1)
            if self.state != "question":
                return

            self.qt -= 1
            if self.qt <= 3:
                sc = pygame.image.load("assets/pictures/question_lowtime.png")  # Timer turns red at the last 3 sec
            else:
                sc = pygame.image.load("assets/pictures/question.png")

            self.screen.blit(sc, (0, 0))
            self.load_question_text(str(self.qt), self.timer_font, center=(971, 183))

        sleep(1)
        if not self.chosen_ans:  # Avoid double answering
            self.sumbit_answer(0)

    def load_question_text(self, text, font, pos=None, center=None, lambda_f=None, bgc=None):
        """
        Render text entry of question screen.

        :param text: text to render
        :param font: font to use
        :param pos: position on screen
        :param center: OR center position
        :param lambda_f: OR lambda expression for calculating position
        :param bgc: background color
        :type text: str
        :type font: pygame.Font
        :type pos: (int, int)
        :type center: (int, int)
        :type lambda_f:
        :type bgc: (int, int, int)
        """
        text = font.render(text, True, (255, 255, 255))

        if center:
            pos = text.get_rect(center=center)
        elif lambda_f:
            text_rect = text.get_rect()
            pos = lambda_f(text_rect.width, text_rect.height)  # pass width and height to the lambda

        if bgc:  # Draw background rectangle
            rect = pygame.Rect(0, 0, 433, 78)

            if center:
                rect.center = center
            elif pos:
                rect = pygame.Rect(pos[0], pos[1], 433, 78)

            pygame.draw.rect(self.screen, bgc, rect, 0)

        self.screen.blit(text, pos)

    def ask_for_match(self) -> None:
        """
        Establish connection with server and ask for match.
        """

        print(f"Loading match screen for topic {self.topic}...")
        self.state = "match"
        self.load_video("assets/videos/match.mp4")
        print("Loaded. Connecting to server...")

        try:
            self.sock = establish_connection(self.name, ip=self.ip)
        except Error.Client.ConnectionFailed:
            self.raise_error()
            return
        except Error.Client.UnexpectedResponse:
            self.raise_error()
            return

        msg = build_message("S", self.topic)
        print("Connection established. Requesting match...")

        # Start another thread to handle connection and update counter
        self.conn_t = MatchThread(self, self.sock, msg)
        self.conn_t.start()

    def load_next_question(self, rsp) -> None:
        """
        Loads next question / game results.
        """

        if rsp.code == "Q":
            # Load question screen
            self.qrsp = rsp
            self.load_question()

        elif rsp.code == "R":
            self.qc = 0  # Reset question count
            self.sock.close()  # Close server connection

            # Load results screen
            print("Loading results screen...")

            if rsp.fields[0] == self.name:
                bg = pygame.image.load("assets/pictures/winner.png")
                self.state = "results-winner"

            elif rsp.fields[0] == "B":
                bg = pygame.image.load("assets/pictures/tie.png")
                self.state = "results-tie"

            else:
                bg = pygame.image.load("assets/pictures/loser.png")
                self.state = "results-loser"

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

    def load_welcome_screen(self) -> None:
        """
        Load welcome screen.
        """

        self.state = "welcome"

        #   Welcome screen:
        print("Loading welcome screen...")
        welcome_bg = pygame.image.load("assets/pictures/welcome.png")
        self.screen.blit(welcome_bg, (0, 0))

        print("Loaded. Waiting for user...")

    def load_topics_screen(self) -> None:
        """
        Load topics screen.
        """

        print("Loading topics screen...")
        sc = pygame.image.load("assets/pictures/topics.png")
        self.screen.blit(sc, (0, 0))
        self.state = "topics"
        print("Loaded. Waiting for user...")

    def load_credits_screen(self):
        """
        Load credits screen.
        """

        print("Loading credits screen...")
        sc = pygame.image.load("assets/pictures/credits.png")
        self.screen.blit(sc, (0, 0))
        self.state = "credits"
        print("Loaded. Waiting for user...")

    def load_sharon_screen(self):
        """
        Load sharon easter egg screen.
        """

        print("Loading sharon screen...")
        sc = pygame.image.load("assets/pictures/sharon.png")
        self.screen.blit(sc, (0, 0))
        self.state = "sharon"
        print("Loaded. Waiting for user...")

    def load_settings_screen(self):
        """
        Load settings screen.
        """

        print("Loading settings screen...")
        sc = pygame.image.load("assets/pictures/settings.png")
        self.screen.blit(sc, (0, 0))
        self.state = "settings"

        # Load textbox
        self.namemgr.value = self.name
        self.namemgr.dehighlight()
        self.namemgr.blit()

        self.ipmgr.value = self.ip
        self.ipmgr.dehighlight()
        self.ipmgr.blit()

        print("Loaded. Waiting for user...")

    def handle_name_typing(self, event):
        """
        Handle typing event on name textbox.
        """

        if event.key == pygame.K_BACKSPACE:
            self.namemgr.value = self.namemgr.value[:-1]
            self.namemgr.blit()

        elif (event.unicode in ascii_letters or event.unicode.isdigit() or event.unicode == "_") and len(self.namemgr.value) < 12:
            self.namemgr.value += event.unicode
            self.namemgr.blit()

        elif event.key == pygame.K_SPACE:
            self.namemgr.value += "_"
            self.namemgr.blit()

        else:
            font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 32)
            text = font.render(hebrew_proof("הזנת תו שגוי"), True,
                               (228, 64, 50))
            self.screen.blit(text, (900, 680))

    def handle_addr_typing(self, event):
        """
        Handle typing event on address textbox.
        """

        if event.key == pygame.K_BACKSPACE:
            self.ipmgr.value = self.ipmgr.value[:-1]
            self.ipmgr.blit()

        elif (event.unicode.isdigit() or event.unicode == ".") and len(self.ipmgr.value) < 15:
            self.ipmgr.value += event.unicode
            self.ipmgr.blit()

        else:
            font = pygame.font.Font("assets/fonts/Ploni/Regular.ttf", 40)
            text = font.render(hebrew_proof("הזנת תו שגוי"), True,
                               (228, 64, 50))
            self.screen.blit(text, (900, 680))

    def handle_mouse_click_on_welcome(self):
        """
        Handle mouse click on welcome screen.
        """

        x, y = pygame.mouse.get_pos()

        if y > 658:
            if x < 124:
                if x < 63:  # Settings button
                    self.load_settings_screen()
                else:  # Credits button
                    self.load_credits_screen()

            elif x >= 1018:  # Sound button
                if self.music_paused:
                    self.music_paused = False
                    pygame.mixer.music.unpause()
                else:
                    self.music_paused = True
                    pygame.mixer.music.pause()

        else:
            self.load_topics_screen()

    def handle_mouse_click_on_settings(self):
        """
        Handle mouse click on settings screen.
        """

        x, y = pygame.mouse.get_pos()

        if 577 < y < 648:
            if 309 < x < 509:  # Cancel button
                self.load_welcome_screen()
                return

            elif 571 < x < 771:  # Confirm button
                self.ip = self.ipmgr.value if len(self.ipmgr.value) > 0 else self.ip
                self.name = self.namemgr.value if len(self.namemgr.value) > 0 else self.name

                self.load_welcome_screen()
                return

        if 164 < x < 580:
            if 354 < y < 412:  # nickname field
                self.state = "settings-name-tb"
                self.namemgr.highlight()
                self.ipmgr.dehighlight()
                return

            elif 433 < y < 491:  # ip field
                self.state = "settings-addr-tb"
                self.ipmgr.highlight()
                self.namemgr.dehighlight()
                return

        self.state = "settings"
        # de-highlight both fields
        self.namemgr.dehighlight()
        self.ipmgr.dehighlight()

    def handle_mouse_click_on_credits(self):
        """
        Handle mouse click on credits screen.
        """

        pos = pygame.mouse.get_pos()
        x, y = pos

        if line_length(pos, (1023, 56)) <= 27:  # If user clicked on close button
            self.load_welcome_screen()

        elif 616 < y < 658 and 688 < x < 956:
            self.load_sharon_screen()

    def handle_mouse_click_on_sharon(self):
        """
        Handle mouse click on sharon screen.
        """

        pos = pygame.mouse.get_pos()

        if line_length(pos, (1023, 56)) <= 27:  # If user clicked on close button
            self.load_credits_screen()

    def handle_mouse_click_on_results(self):
        """
        Handle mouse click on results screen.
        """

        x, y = pygame.mouse.get_pos()

        if self.state == "results-winner":
            if 365 < x < 532 and 503 < y < 563:
                self.ask_for_match()

            elif 144 < x < 312 and 503 < y < 563:
                self.load_welcome_screen()

        elif self.state == "results-tie":
            if 789 < x < 957 and 580 < y < 639:
                self.ask_for_match()

            elif 569 < x < 737 and 580 < y < 639:
                self.load_welcome_screen()

        elif self.state == "results-loser":
            if 789 < x < 957 and 494 < y < 554:
                self.ask_for_match()

            elif 569 < x < 737 and 494 < y < 554:
                self.load_welcome_screen()

    def handle_mouse_click_on_match(self):
        """
        Handle mouse click on match screen.
        """

        x, y = pygame.mouse.get_pos()

        if 478 < x < 602 and 633 < y < 677:  # If user clicked on cancel button
            # Stop looking for a match and alert the server
            self.conn_t.stop()

            # Load topics screen
            self.stop_video()
            self.load_topics_screen()

    def handle_mouse_click_on_topic(self) -> None:
        """
        Handle mouse click on topic screen.
        """

        pos = pygame.mouse.get_pos()

        if line_length(pos, (1023, 56)) <= 27:  # If user clicked on close button
            self.load_welcome_screen()

        else:
            self.topic = click_in_bounds(pos)

            if self.topic:
                self.ask_for_match()

    def sumbit_answer(self, ans) -> None:
        """
        Send answer to the server.

        :param ans: chosen answer (1-4), 0 if none chosen
        :type ans: int
        """

        send_message(self.sock, SID, build_message("A", ans))  # Send answer to server

        if ans != 0:
            self.load_question_text(hebrew_proof(self.qrsp.fields[ans]), self.answers_font, center=ANS_CENT[ans - 1],
                                    bgc=(134, 170, 223))  # Highlight chosen answer

        # Wait for the next question / game results
        rsp = recv_message(self.sock, SID, timeout=TIMEOUT + ANS)

        if ans != 0:
            results_ptr = 5 if rsp.code == "Q" else 1
            if int(rsp.fields[results_ptr]) == ans:
                self.load_question_text(hebrew_proof(self.qrsp.fields[ans]), self.answers_font, center=ANS_CENT[ans - 1],
                                        bgc=(0, 128, 55))
            else:
                self.load_question_text(hebrew_proof(self.qrsp.fields[ans]), self.answers_font, center=ANS_CENT[ans - 1],
                                        bgc=(228, 64, 50))

        sleep(0.3)
        self.load_next_question(rsp)  # Load next question / game results

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
                            self.handle_mouse_click_on_welcome()

                        elif self.state == "topics":
                            self.handle_mouse_click_on_topic()

                        elif self.state == "question":
                            ans = chosen_answer(pygame.mouse.get_pos())

                            if ans and not self.chosen_ans:
                                self.chosen_ans = True
                                a_t = threading.Thread(target=self.sumbit_answer, args=(ans,))
                                a_t.start()

                        elif self.state.startswith("settings"):
                            self.handle_mouse_click_on_settings()

                        elif self.state == "credits":
                            self.handle_mouse_click_on_credits()

                        elif self.state == "sharon":
                            self.handle_mouse_click_on_sharon()

                        elif self.state == "match":
                            self.handle_mouse_click_on_match()

                        elif self.state.startswith("results"):
                            self.handle_mouse_click_on_results()

                elif event.type == pygame.KEYDOWN:  # Handle typing
                    if self.state == "settings-name-tb":
                        self.handle_name_typing(event)

                    elif self.state == "settings-addr-tb":
                        self.handle_addr_typing(event)

            pygame.display.flip()  # Update screen


def main():
    gui = Gui()
    gui.run()


if __name__ == "__main__":
    main()
