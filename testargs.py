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
channel_id: vuzs-1412
bank: ВУЗ
office: ОО Университетский
event_id: 1111112
hub: ДО Уралмаш
channel_type: Основной
event_datetime: 2014.12.22 01:05:12
office_comments:  Длительность более 8 часов
"""]

testargs_ChannelUP = ["",
            "kspd-tracker",
            "ChannelUP",
"""channel_id: vuzs-1412
event_id: 1111112
event_recovery_datetime: 2014.12.23 03:05:12
event_age: 22h 0m
status_id: 10
night_status_id: 5
night_channel_reason: В нерабочее время
"""]

testargs_ChannelDOWNnight = ["",
            "kspd-tracker",
            "ChannelDOWN",
            """project_id: 2
tracker_id: 6
status_id: 1
priority_id: 2
assigned_to_id: 6
watcher_user_ids:
channel_id: vuzs-1422
bank: ВУЗ
office: ОО Троицкий
event_id: 12345678
hub: ЦО
channel_type: Основной
event_datetime: 2014.12.21 22:05:12
office_comments:  Ночь
"""]

testargs_ChannelUPnight = ["",
            "kspd-tracker",
            "ChannelUP",
"""channel_id: vuzs-1422
event_id: 12345678
event_recovery_datetime: 2014.12.22 03:15:12
event_age: 5h 10m
status_id: 10
night_status_id: 5
night_channel_reason: В нерабочее время
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
event_datetime: 2014.12.24 13:02:04
office_comments:
"""]

testargs_OfficeUP = ["",
            "kspd-tracker",
            "OfficeUP",
"""office_id: vuzs-1410
event_id: 544445
event_recovery_datetime: 2014.12.25 17:53:04
event_age: 1d 4h 51m
status_id: 10
night_status_id: 5
night_office_reason: В нерабочее время
"""]

testargs_OfficeDOWNnight= ["",
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
event_datetime: 2014.12.24 23:02:04
office_comments:
"""]

testargs_OfficeUPnight = ["",
            "kspd-tracker",
            "OfficeUP",
"""office_id: vuzs-1410
event_id: 544445
event_recovery_datetime: 2014.12.25 00:53:04
event_age: 1h 51m
status_id: 10
night_status_id: 5
night_office_reason: В нерабочее время
"""]