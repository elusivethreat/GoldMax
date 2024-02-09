import multiprocessing
from cmd import Cmd
from time import sleep
from colorama import Fore as Color
from toolbox.GoldHttp import start_http
from pyfiglet import Figlet
from prettytable import PrettyTable as Table
from base64 import b64encode


def goldmax_cli():
    print(Color.BLUE)
    prompt = GoldMaxPrompt()
    prompt.banner()
    bash_prompt = Color.LIGHTBLUE_EX + '┌──(' + Color.RED + 'GoldMax' + Color.LIGHTBLUE_EX + ')─[~]' + '\n' + '└─$ '
    prompt.prompt = Color.BLUE + bash_prompt
    prompt.cmdloop()


class GoldMaxPrompt(Cmd):
    def __init__(self):
        self.agent = None
        self.job = None
        self.http_server = None
        self.state = False
        self.commands = ['Idle', 'Execute', 'Start', 'Read', 'Update', 'Write']
        super().__init__()

    @staticmethod
    def banner():
        f = Figlet(font='shadow')
        print(Color.BLUE + f.renderText('GoldMax') + Color.RESET)

    def emptyline(self) -> bool:
        return False

    def do_exit(self, inp) -> bool:
        """Shutting Down Arc Reactor"""
        self.do_stop(inp)
        return True

    def do_commands(self, inp):
        """
        Display supported GoldMax commands
        """
        print("[+] Available Commands: [+]")
        for cmd in self.commands:
            print(Color.YELLOW, cmd, Color.RESET)

    def do_stop(self, arg):
        """Shutdown All Active Servers"""
        print(Color.RED, "Shutting Down any active servers...")
        if self.http_server:
            self.http_server.terminate()
            # Allow time to update state
            sleep(2)
            http_status = self.http_server.is_alive()

            if http_status is False:
                print(Color.GREEN, "Complete! HTTP server shutdown successfully")
        else:
            print(Color.YELLOW, "No servers running", Color.RESET)

    def do_start(self, arg):
        """
        Start C2 Servers (HTTP and DNS servers)
        """
        http_port = 443
        active_servers = []
        start_http()
        """
        if not self.http_server:
            # HTTP Server
            http_proc = multiprocessing.Process(target=start_http)
            http_proc.start()
            active_servers.append(http_proc)
            self.http_server = http_proc
        """
        print(Color.LIGHTGREEN_EX, f"Server started:", Color.RESET)
        print(Color.WHITE, f" HTTP Listener on {http_port}", Color.RESET, Color.RESET)


if __name__ == "__main__":
    goldmax_cli()
    
    