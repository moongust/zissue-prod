# -*- coding: UTF-8 -*-
__author__ = 'Amv'

testargs_ChannelDOWN = ["",
            "kspd-tracker",
            "ChannelDOWN",
            """project_id: 2
tracker_id: 6
status_id: 1
priority_id: 2
assigned_to_id: 6
watcher_user_ids:
channel_id: vuzs-1410
bank: ВУЗ
office: ОО Победный
event_id: 222222
hub: ЦО
channel_type: Основной
event_datetime: 2014.12.22 01:05:12
office_comments:  Нет комментариев
"""]

testargs_ChannelUP = ["",
            "kspd-tracker",
            "ChannelUP",
"""channel_id: vuzs-1410
event_id: 222222
event_recovery_datetime: 2014.12.22 03:05:12
event_age: 25d 14h 51m
status_id: 10
night_status_id: 5
night_reason: В нерабочее время
"""]

testargs_OfficeDOWN= ["",
            "kspd-tracker",
            "OfficeDOWN",
            """project_id: 2
tracker_id: 5
status_id: 1
priority_id: 4
assigned_to_id: 6
watcher_user_ids:
office_id: 1410
bank: ВУЗ
office: ЦО
event_id: 544445
event_datetime: 2014.12.24 01:02:04
office_comments:  Нет комментариев
"""]

testargs_OfficeUP = ["",
            "kspd-tracker",
            "OfficeUP",
"""office_id: vuzs-1410
event_id: 544445
event_recovery_datetime: 2014.12.24 05:53:04
event_age: 4h 51m
status_id: 10
night_status_id: 5
night_reason: В нерабочее время
"""]
