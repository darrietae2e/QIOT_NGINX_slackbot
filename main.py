from flask import json
import time
import requests
from datetime import datetime, timedelta

# This python process will serve to request information from the slack channels, retrieve the messages,
# count them and post a messagge in the same channel alerting the message count containing the specific values.

# =-=-=-=-=-=-=-=-=-=-=- PRD VARIABLES
slack_token = 'xoxp-12000902535-12003995728-267908577444-a7ac8589736c78ebe2e98a128b4437ab'
slack_hook = 'https://hooks.slack.com/services/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'
prd_hook = 'https://hooks.slack.com/services/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'
channel = 'C7NKM13KR'
msg_count = 5
bot_id = "B7LTJGT7S"


def get_messages():
    # gather all messages from slack from the last minute.
    date_last = datetime.now() - timedelta(minutes=1)
    ts_last = time.mktime(date_last.timetuple())
    payload = {'token': slack_token, 'channel': channel, "oldest": ts_last}
    try:
        messages = requests.get(url='https://slack.com/api/' + 'channels.history', params=payload)
        msg_list = messages.json()['messages']
        # returns a list of messages only, takes out unnecessary info from slack.
        print("Messages from slack")
        print(json.dumps(msg_list, indent=4))
        return msg_list
    except Exception as e:
        print("something happened, request to slack didn't happen: " + str(e))


def filter_nginx():
    # check only Nginx related messages
    nginx_msgs = []
    slack_list = get_messages()
    if slack_list:
        for msg in slack_list:
            if 'bot_id' in msg:
                if msg['bot_id'] == bot_id:
                    nginx_msgs.append(msg)
        if nginx_msgs:
            # print(json.dumps(nginx_msgs, indent=4))
            return nginx_msgs
        else:
            print("no messages contain 'Nginx' on slack messages")
            return None
    else:
        print("no messages from slack")


def extract_min(take=0):
    # look for more than 5 msgs in a minute span
    nginx_msgs = filter_nginx()
    for i in range(take):
        if nginx_msgs:
            nginx_msgs.pop(0)
        else:
            break
    if nginx_msgs and len(nginx_msgs) >= msg_count:
        nginx_min = []
        old = nginx_msgs[0]
        for x in nginx_msgs:
            if float(x['ts']) < (float(old['ts']) + 60):
                nginx_min.append(x)
        if len(nginx_min) >= msg_count:
            return nginx_min
        else:
            extract_min((take+1))
    else:
        print("not enough msgs in filtered nginx list")
        return None


def get_env():
    envs = []
    minute_msgs = extract_min()
    if minute_msgs:
        for m in minute_msgs:
            if m['text']:
                env_name = m['text'][41:44]
                if envs:
                    found = False
                    for e in envs:
                        if e['name'] == env_name:
                            found = True
                            if e['list']:
                                e['list'].append(m)
                            else:
                                e['list'] = [m]
                        else:
                            pass
                    if not found:
                        envs.append({'name': env_name, 'list': [m]})
                else:
                    envs.append({'name': env_name, 'list': [m]})
        if envs:
            # print(json.dumps(envs, indent=4))
            return envs
        else:
            print("nothing in envs")
            return None
    else:
        print("no msgs on minute list")
        return None


def get_container():
    result = []
    nginx_envs = get_env()
    if nginx_envs:
        for env in nginx_envs
            if env['list']:
                containers = []
                for msg in env['list']:
                    if msg['text']:
                        # t container id
                        conn_id = msg['text'][16:27]
                        if containers:
                            found = False
                            for c in containers:
                                if c['id'] == conn_id:
                                    c['times'] = int(c['times']) + 1
                                    found = True
                            if not found:
                                containers.append({'id': conn_id, "times": 1})
                        else:
                            containers.append({'id': conn_id, "times": 1})
                if containers:
                    env['containers'] = containers
            else:
                print("something happened, env came with nothing")
        if nginx_envs:
            print("exporting minute report")
            # print(json.dumps(nginx_envs, indent=4))
            export_min_report(nginx_envs)
    else:
        print("Something happened, no environments.")


def export_min_report(envs):
    # has to report the amount of reloading Nginx messages organized by environment.
    attachments = []
    if envs:
        for e in envs:
            if e['name'] == "prd":
                print("check_prd")
                check_prd(e)
            else:
                string = ""
                for c in e['containers']:
                    string += " \n\t container " + c['id'] + " has reloaded " + str(c['times']) + " times"
                attachments.append({
                    "text": "On environment " + e['name'] + string,
                    "color": "danger"
                })
        slack_msg = {
            "text": "More than " + str(msg_count) + " messages in the last minute",
            "attachments": attachments
        }
        if attachments:
            try:
                res = requests.post(slack_hook, json.dumps(slack_msg))
                print("Slack response" +  str(res))
            except Exception as e:
                print("Error: " + str(e))
        else:
            print("cant post no attachments, probably prd notifications")
    else:
        print("Can't print if there are no containers.")


def check_prd(env):
    # handles only the prd related notifications
    attachments = []
    times = 0
    for c in env['containers']:
        times += int(c['times'])
        string = " \n\t container " + c['id'] + " has reloaded " + str(c['times']) + " times"
        attachments.append({"text": string, "color": "danger"})
    if times >= msg_count:
        slack_data = {
            "text": "More than " + str(msg_count) + " prd NGINX messages in the last minute",
            "attachments": attachments
        }
        try:
            # will post only to the prd designated channel
            print("posting to prd webhook")
            requests.post(prd_hook, json.dumps(slack_data))
        except Exception as e:
            print("Something happened: " + str(e))
    else:
        print("Not enough messages from production")


def main():
    while True:
        print("Start!")
        get_container()
        time.sleep(60)  # seconds between every run.


main()
