
import functools
import logging
import os
import time
import traceback

import requests

LOG = logging.getLogger(__name__)

def slack_notify(channel, hook):
    def decorator_slack_notify(func):
        @functools.wraps(func)
        def wrapper_slack_hook(*args, **kwargs):
            if kwargs.get("region"):
                region = kwargs.get("region")
            else:
                region = args[0]

            if kwargs.get("zone"):
                zone = kwargs.get("zone")
            else:
                zone = args[1]

            cli = SlackClient(defaults={"channel": channel, "hook": hook})
            cli.post_webhook_message(
                "",
                attachments=[
                    {"text": "Starting update on region={!r} zone={!r}".format(region, zone),
                     "color": "good"}
                ]
            )

            start_time = time.perf_counter()

            try:
                wrap_return = func(*args, **kwargs)
            except Exception:
                cli.post_webhook_message(
                    "",
                    attachments=[
                        {"text": "Exception during update region={!r} zone={!r}\n```{}```".format(
                            region, zone, traceback.format_exc()),
                         "color": "danger"}
                    ]
                )
                raise

            run_time = time.perf_counter() - start_time
            cli.post_webhook_message(
                "",
                attachments=[
                    {"text": "Finished update on region={!r} zone={!r} in {:.4f} secs".format(region, zone, run_time),
                     "color": "good"}
                ]
            )

            return wrap_return
        return wrapper_slack_hook
    return decorator_slack_notify

class SlackClient(object):

    def __init__(self, token="", defaults=None):
        if defaults is None:
            defaults = {}

        self._Token = token
        # this is defaults and limits the keys that can be used
        self._Defaults = {
            "channel": os.getenv("SLACK_HOOK_CHANNEL"),
            "hook": os.getenv("SLACK_HOOK_URL"),
            "write_function": self.post_webhook_message}
        if defaults:
            self.set_defaults(defaults=defaults)
        self._check_slack_cfg()

    def _check_slack_cfg(self):
        if self._Defaults['channel'] is None or self._Defaults['hook'] is None:
            raise ValueError((f"Invalid Slack configuration. "
                              f"Hook {self._Defaults['hook']} "
                              f"Channel {self._Defaults['channel']}"))

    def write(self, *argv, **kwargs):
        wf =self._Defaults.get("write_function", None)
        if wf:
            return wf(*argv, **kwargs)

    def _encode(self, msg):
        """
        Encode Slack control characters as HTML entities.
        See: https://api.slack.com/docs/message-formatting#how_to_escape_characters
        """

        msg = msg.replace('&', '&amp;')
        msg = msg.replace('<', '&lt;')
        msg = msg.replace('>', '&gt;')

        return msg

    def set_defaults(self, defaults={}):
        for k, v in defaults.items():
            if k in self._Defaults:
                self._Defaults[k] = v

    def post_event_message(self, **kwargs):
        color = kwargs.get("color", "good")
        msg = kwargs.get("description", "")
        if msg:
            self.post_webhook_message("", attachments=[
                {"text": "```{}```".format(msg), 
                "color": color
                }]
            )

    def post_webhook_message(
            self, body_text,
            attachments=None, channel="", hook=""):

        if attachments is None:
            attachments = []
        hook = hook if "" != hook else self._Defaults.get("hook", "")
        channel = channel if "" != channel else self._Defaults.get("channel", "")
        if not hook or not channel:
            return

        headers = {
            'Content-type': 'application/json; charset=utf-8',
        }

        payload = {
            "channel": channel,
            "text": self._encode(body_text),
        }

        message_att = []
        for a in attachments:
            if isinstance(a, str):
                message_att.append(
                    {"text": self._encode(a) , "mrkdwn_in": ["text"]}
                )
            elif isinstance(a, dict):
                message_att.append(
                    {
                        "text": self._encode(a.get("text", "")),
                        "mrkdwn_in": ["text"],
                        "color": a.get("color", "good"),
                    }
                )

        if message_att:
            payload["attachments"] = message_att

        try:
            requests.post(
                hook,
                headers=headers,
                json=payload,
            )

        except requests.exceptions.RequestException as e:
            LOG.info(e)
            raise
