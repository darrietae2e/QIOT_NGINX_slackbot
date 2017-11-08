from flask import json
import requests

slack_hook = "https://hooks.slack.com/services/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"


def send_notification_dev(amount):
    for i in range(amount):
        notification = {
            "username": "NginxTest",
            "text": "Nginx container e25f61632018 reloaded in dev environment because it detected IPs changes"
        }
        try:
            requests.post(slack_hook, json.dumps(notification))
        except Exception as e:
            print("Error " + str(e))


def send_notification_stg(amount):
    for i in range(amount):
        notification = {
            "username": "NginxTest",
            "text": "Nginx container fdd1b3174e1e reloaded in stg environment because it detected IPs changes"
        }
        try:
            requests.post(slack_hook, json.dumps(notification))
        except Exception as e:
            print("Error " + str(e))


def send_notification_prd(amount):
    for i in range(amount):
        notification = {
            "username": "NginxTest",
            "text": "Nginx container 324ef41cc6bb reloaded in prd environment because it detected IPs changes"
        }
        try:
            requests.post(slack_hook, json.dumps(notification))
        except Exception as e:
            print("Error " + str(e))


def main():
    send_notification_dev(0)
    send_notification_stg(0)
    send_notification_prd(7)


main()
