import json
import redis
import random
import string
import base64
from datetime import datetime
from typing import Dict

"""
Redis helper functions for managing DB

v.0.0.1

DB Structure:

    Tables:

        (Agents):
            {
                'Agent': Unique UUID,
                'LastCheckIn': TimeStamp,
                'CheckIn': Total number of beacons,
                'C2': Domain for comms
            }

        (Pending / Active / Done):
            {
                paw: Unique UUID
                cmd: Command for Execution   
            }
"""


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def drop_table(table):
    """

    :param table:
    :return:
    """

    redis_client = redis.Redis(host='localhost', port=7001, db=0)
    try:
        redis_client.delete(table)
    except AssertionError:
        return True


def update_redis(redis_key: str, update_dict: Dict):
    """
    Delete data from redis database and update that key.
    Extract data needed before calling this function
    :return: None
    """
    redis_client = redis.Redis(host='localhost', port=7001, db=0)

    redis_client.delete(redis_key)
    redis_client.set(redis_key, json.dumps(update_dict))


def get_agents(conn='localhost'):
    """
    Queries the Agent Table and returns all active agents
    :param conn:
    :return:
    """
    active_agents = {}
    redis_client = redis.Redis(host=conn, port=7001, db=0)
    redis_key = 'Agents'

    if redis_client.get(redis_key):
        active_agents = json.loads(redis_client.get(redis_key).decode())

    return active_agents


def update_agent(agent_name: str, c2, conn='localhost'):
    """
    Manages the Agent Table for tracking active implants
    :param agent_name:
    :param c2: Store Host specific information
    :param conn: IP address for Redis instance
    :return:
    """
    redis_client = redis.Redis(host=conn, port=7001, db=0)
    redis_key = 'Agents'
    # C2 Domain for Agent
    domain = c2
    time = str(datetime.now())
    holdAgentName = {}
    redis_agents = {}
    count = 0

    if redis_client.get(redis_key):
        redis_agents = json.loads(redis_client.get(redis_key).decode())

        for aKey, aVal in redis_agents.items():
            holdAgentName[aKey] = [aVal['C2'], aVal['Agent']]

        for haKey, haVal in holdAgentName.items():
            count = count + 1

            if (agent_name == haVal[1]) and (haVal[0] == domain):
                redis_agents[haKey]['CheckIn'] = int(redis_agents[haKey]['CheckIn']) + 1
                redis_agents[haKey]['LastCheckIn'] = time
                break

            elif count == (len(holdAgentName)):
                # If there are no matches in the database then it is a new agent
                redis_agents[int(haKey) + 1] = {'Agent': agent_name,
                                                'LastCheckIn': time,
                                                'CheckIn': 1,
                                                'C2': domain
                                                }

    else:
        # first agent means first entry in the database
        redis_agents[1] = {'Agent': agent_name,
                           'LastCheckIn': time,
                           'CheckIn': 1,
                           'C2': domain
                           }

    update_redis(redis_key, redis_agents)


def get_next_index(table):
    """
    Used for tracking next index for inserting new jobs
    :param table:
    :return:
    """
    # Check if we already have jobs
    redis_client = redis.Redis(host='localhost', port=7001, db=0)
    jobs = redis_client.get(table)
    # Start index after last known job if any
    try:

        if jobs:
            all_jobs = json.loads(jobs.decode())
            last_index = int(list(all_jobs.keys())[-1])
            count = last_index + 1
            return count
        else:
            return '1'

    except (IndexError, ValueError):

        return '1'


def _get_items(table):
    redis_client = redis.Redis(host='localhost', port=7001, db=0)
    pending = redis_client.get(table)

    if pending:
        return json.loads(pending.decode())
    else:
        return {}


def _update_table(table, jobs):
    """
    Move job from one "Status" to the next phase
    Pending -> Active -> Done
    :return:
    """
    current_jobs = _get_items(table)

    # Other jobs found in DB, append new jobs
    if current_jobs:

        for job in jobs.values():
            index = get_next_index(table)
            # Add new jobs to the current
            current_jobs.update({index: job})

            update_redis(table, current_jobs)

    # No jobs found, insert fresh jobs
    else:
        update_redis(table, jobs)


def get_jobs(uuid='None', conn='localhost'):
    """
    Extract jobs from Pending and moves to "Active" state in Redis
    :param uuid: Pull jobs related for specific Implant/Agent set.. (GoldMax, SolarEclipse)
    :param conn: IP address for RedisDB
    :return:
    """
    redis_client = redis.Redis(host=conn, port=7001, db=0)
    agent_jobs = {}
    active_jobs = {}

    if redis_client.keys('Pending'):
        pending = json.loads(redis_client.get('Pending').decode())
        # The database will be updated with the information in the targets Dictionary.
        for pKey, pVal in pending.items():
            target = pVal['paw']
            if uuid in target:
                agent_jobs[pKey] = pVal

        if agent_jobs:
            # Move jobs from Pending to Active dictionary
            for hpKey, hpVal in agent_jobs.items():
                active_jobs[hpKey] = hpVal
                pending.pop(hpKey)

            # Removes jobs from Pending
            if pending:
                # if any changes are needed
                update_redis('Pending', pending)
            else:
                # if there are no more pending jobs delete "Pending" from redis
                redis_client.delete('Pending')

            # Add jobs to Active table
            _update_table('Active', active_jobs)

            return active_jobs


def _find_jobs(agent=None, table='Active'):
    """
    Extract specific job for agent
    :param job:
    :return:
    """
    found = []
    jobs = _get_items(table)

    for index, job in jobs.items():
        if job['paw'] == agent:
            found.append(job)

    return found


def find_job(agent=None, table='Active', cmd=None):
    """
    Default table is Active; Pull all jobs for a specific agent
    :param agent:
    :param table:
    :param cmd:
    :return:
    """

    jobs = _find_jobs(agent, table)

    for job in jobs:
        if cmd == job['cmd'][0]:
            return job


def find_agent(domain):
    """
    Find agent based on C2 Domain
    :param domain:
    :return:
    """
    agents = _get_items('Agents')

    for agent in agents.values():
        if agent['C2'] == domain:
            return agent['Agent']


def insert_jobs(agent: str, job: dict):
    """
    Jobs
    :param agent
    :param job:
    :return: dict
    """

    redis_client = redis.Redis(host='localhost', port=7001, db=0)

    pending_jobs = _get_items('Pending')

    index = get_next_index('Pending')

    next_job = {index: {'paw': agent,
                        'id': id_generator(),
                        'cmd': job
                        }
                }

    if pending_jobs:
        pending_jobs.update({index: next_job[index]})
        update_redis('Pending', pending_jobs)

    else:
        update_redis('Pending', next_job)


def store_job_results(agent_name, results, conn='localhost'):
    """
    Used for CALDERA
    :return:
    """
    redis_client = redis.Redis(host=conn, port=7001, db=0)
    active_jobs = {}
    completed_jobs = {}

    if redis_client.keys('Active'):
        redisActive = json.loads(redis_client.get('Active').decode())

        for aKey, aVal in redisActive.items():
            target = aVal['paw']
            if agent_name in target:
                active_jobs[aKey] = aVal
                """ Specific to GoldMax
                bad_response = [b'\x0b', b'\x10']
                for byte in bad_response:
                    if byte in results:
                        results = results.replace(byte, b'')
                """
        for hKey, hVal in active_jobs.items():
            completed_jobs[hKey] = {'paw': hVal['paw'],
                                    'id': hVal['id'],
                                    'output': base64.b64encode(results).decode()
                                    }
            redisActive.pop(hKey)

        if redisActive:
            update_redis('Active', redisActive)
        else:
            redis_client.delete('Active')

        if redis_client.keys('Done'):
            redisDone = json.loads(redis_client.get('Done').decode())
            for hdKey, hdVal in completed_jobs.items():
                redisDone[hdKey] = hdVal
            update_redis('Done', redisDone)
        else:
            redis_client.set('Done', json.dumps(completed_jobs))

