import enum


class MessageAdapter(str, enum.Enum):
    SLACK = "Slack"