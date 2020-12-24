
import functools
import logging
import os
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

import requests

LOG = logging.getLogger(__name__)

class SlackClient(object):

    def __init__(self, token: str = "", defaults: Dict = None) -> None:
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

    def _check_slack_cfg(self) -> None:
        if self._Defaults['channel'] is None or self._Defaults['hook'] is None:
            raise ValueError((f"Invalid Slack configuration. "
                              f"Hook {self._Defaults['hook']} "
                              f"Channel {self._Defaults['channel']}"))

    def write(self, *argv: str, **kwargs: str) -> None:
        wf: Any = self._Defaults.get("write_function", None)
        if wf:
            wf(*argv, **kwargs)

    def _encode(self, msg: str) -> str:
        """
        Encode Slack control characters as HTML entities.
        See: https://api.slack.com/docs/message-formatting#how_to_escape_characters
        """

        msg = msg.replace('&', '&amp;')
        msg = msg.replace('<', '&lt;')
        msg = msg.replace('>', '&gt;')

        return msg

    def set_defaults(self, defaults: Dict = {}) -> None:
        for k, v in defaults.items():
            if k in self._Defaults:
                self._Defaults[k] = v

    def post_event_message(self, **kwargs: str) -> None:
        color = kwargs.get("color", "good")
        msg = kwargs.get("description", "")
        if msg:
            self.post_webhook_message("", attachments=[
                {"text": "```{}```".format(msg), 
                "color": color
                }]
            )

    def post_webhook_message(self, body_text: str, attachments: Optional[List] = None,
                             channel: str = "", hook: str = "") -> None:

        if attachments is None:
            attachments = []
        # not sure why mypy does not like the following 2 lines, assigning str to str
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
