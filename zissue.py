#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
sys.argv[1] - To - URL:redmine API key, or "kspd-tracker"
sys.argv[2] - Subject - [ChannelDOWN|ChannelUP|OfficeDOWN|OfficeUP]
sys.argv[3] - Body - set of lines

1) Channel DOWN message,
To = kspd-tracker
Subject = ChannelDOWN
Body =
project_id: 2
tracker_id: 6
status_id: 1
priority_id: 2
assigned_to_id: 6
watcher_user_ids:
channel_id: {INVENTORY.SITE.ZIP}
bank: {INVENTORY.SITE.ADDRESS.A}
office: {INVENTORY.SITE.ADDRESS.B}
event_id: {EVENT.ID}
hub: {INVENTORY.SITE.ADDRESS.C}
channel_type: {INVENTORY.SITE.NOTES}
event_datetime: {EVENT.DATE} {EVENT.TIME}
office_comments:  {INVENTORY.POC.PRIMARY.NOTES}

fields = "message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
         "channel_id bank office event_id hub channel_type event_date event_time office_comments"

2) Channel UP message, Subject -> message_type = ChannelUP
To = kspd-tracker
Subject = ChannelUP
Body =
event_id: {EVENT.ID}
channel_id: {INVENTORY.SITE.ZIP}
event_recovery_datetime: {EVENT.RECOVERY.DATE} {EVENT.RECOVERY.TIME}
event_age: {EVENT.AGE}
status_id: 10
night_status_id: 5
night_channel_reason: В нерабочее время

fields = "message_type channel_id event_id event_recovery_date event_recovery_time event_age status_id"
         "night_status_id, night_reason"

3) Office DOWN message, Subject -> message_type = OfficeDOWN
To = kspd-tracker
Subject = ChannelDOWN
Body =
project_id: 2
tracker_id: 5
status_id: 1
priority_id: 4
assigned_to_id: 6
watcher_user_ids:
office_id: {INVENTORY.SITE.ZIP}
bank: {INVENTORY.SITE.ADDRESS.A}
office: {INVENTORY.SITE.ADDRESS.B}
event_id: {EVENT.ID}
event_datetime: {EVENT.DATE} {EVENT.TIME}
office_comments:  {INVENTORY.POC.PRIMARY.NOTES}

fields = "message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
         "office_id bank office event_id event_date event_time office_comments"

4) Office UP message, Subject -> message_type = OfficeUP
To = kspd-tracker
Subject = ChannelDOWN
Body =
event_id: {EVENT.ID}
office_id: {INVENTORY.SITE.ZIP}
event_recovery_datetime: {EVENT.RECOVERY.DATE} {EVENT.RECOVERY.TIME}
event_age: {EVENT.AGE}
status_id: 10
night_status_id: 5
night_office_reason: В нерабочее время

fields = "message_type office_id event_id event_recovery_date event_recovery_time event_age status_id"
         "night_status_id, night_reason"

Установка:
1) переписать скрипт в каталог скриптов заббикса (вероятно /usr/lib/zabbix/alertscripts)
2) сменить владельца и группу на zabbix.zabbix: chown zabbix:zabbix zissue.py
3) установить для файла права на выполнение chmod ug+x zissue.py
4) проверить ls -la наличие права на чтение и запуск и у группы zabbix
5) добавить в файл /etc/rsyslog.conf строку: local4.*   /var/log/zissue.log, перезапустить службу rsyslog
    service restart rsyslog
6) Настроить zabbix
"""

import redmine
import logging
import logging.handlers
import sys
import os
import time
#import testargs
import datetime

VERSION="0.2 rev5"

OPTIONS = dict(
    log2console = False,                 # True for test purposes
    loghandler="FileHandler",           # Обработчик логов, FileHandler or SysLogHandler,
    #logdir="C:/Amv/Temp/zissue/log",    # Каталог для логфайлов или
    logdir="/var/log/zabbix/zissue",
    #loghandler="SysLogHandler",
    syslogdir="/dev/log",               # сокет для SysLogHandler или адрес внешнего сервера
    facility = "LOG_LOCAL4",            # facility для SysLogHandler
    logname="zissue",                   # logger name, filename for FileHandler
    #tmpdir="C:/Amv/Temp/zissue/temp",   # Каталог временных файлов
    tmpdir="/tmp",                      # Каталог временных файлов
    #loglevel="DEBUG",                   # Уровень логирования (DEBUG for test purposes)
    loglevel="INFO",                   # Уровень логирования (DEBUG for test purposes)
    archivelog=False,  # Архивирование логфайлов после ? нереализовано, требует доработки...
    server="http://kspd-tracker.life.corp",
    key="1b2fb6be316492751a29bf119a1b2f9ca108ad49",
    ChannelDOWN="message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
                "channel_id bank office event_id hub channel_type event_datetime office_comments",
    ChannelDOWN_int="project_id tracker_id status_id priority_id assigned_to_id",
    ChannelDOWN_intlist="watcher_user_ids",
    ChannelUP="message_type channel_id event_id event_recovery_datetime event_age status_id night_status_id "
              "night_channel_reason",
    ChannelUP_int="status_id",
    ChannelUP_intlist="",
    OfficeDOWN="message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
               "office_id bank office event_id event_datetime office_comments",
    OfficeDOWN_int="project_id tracker_id status_id priority_id assigned_to_id",
    OfficeDOWN_intlist="watcher_user_ids",
    OfficeUP="message_type office_id event_id event_recovery_datetime event_age status_id night_status_id "
             "night_office_reason",
    OfficeUP_int="status_id",
    OfficeUP_intlist="",
    custom_fields = dict(channel_id=10,bank=2,office=1,event_id=9,hub=12,
                         channel_type=11,office_comments=23,event_datetime=7,event_recovery_datetime=8,
                         event_age=6, channel_reason=20, office_reason=4),
    Office_DOWN_subject_template = "Zabbix: Офис {0[bank]} {0[office]} {0[office_id]} DOWN",
    Office_DOWN_description_template =
                            "Zabbix: Офис {0[bank]} {0[office]} {0[office_id]} DOWN, event_id: {0[event_id]}\n"
                            "Event started at {0[event_datetime]}",
    Office_UP_description_template = "Zabbix: Офис {0[office_id]} UP, event_id: {0[event_id]}, recovery_datetime: "
                                      "{0[event_recovery_datetime]}",
    Channel_DOWN_subject_template = "Zabbix: Канал {0[bank]} {0[office]} {0[channel_id]} DOWN",
    Channel_DOWN_description_template =
                            "Zabbix: Канал {0[bank]} {0[office]} {0[channel_id]} DOWN, event_id: {0[event_id]}\n"
                            "Event started at {0[event_datetime]}",
    Channel_UP_description_template = "Zabbix: Канал {0[channel_id]} UP, event_id: {0[event_id]}, recovery_datetime: "
                                      "{0[event_recovery_datetime]}",
    date_format = "%Y.%m.%d %H:%M:%S"       # нужен
)

# Определение констант
P_DOWN = 0      # для pmode
P_UP = 1        # для pmode
P_OFFICE = 0    # для ptype
P_CHANNEL = 1   # для ptype

M_DOWN_NEW = 1
M_DOWN_APPEND = 2
M_UP_APPEND = 3
M_DOWN_NEW_NODIR = 4
M_UP_NODIR = 5
M_UP_NOFILE = 6
M_PASS = 0

# Определение классов ошибок
class ArgvError(Exception):
    pass  # Ошибка в количестве аргументов

class IssueError(Exception):
    pass  # Ошибка в подсистеме

class Issue(object):
    """
    Класс инкапсулирует понятие Событие=задача в Redmine
    При всех ошибках генерируется EventFileError
    """

    def __init__(self, parameters, options, logger):
        """
        Инициализация класса: проверка каталога, вычисление issuemode и issuenum, другие вспомогательные элементы
        """
        logger.debug("issue.__init__ started")
        self.parameters = parameters # массив полученных от zabbix параметров
        self.options = options
        self.logger = logger
        self.tmpdir = self.options["tmpdir"].replace("/", os.sep)
        self.filename = self.tmpdir + os.sep + parameters["event_id"]
        # self.pmode,  DOWN или UP,
        # self.ptype,  office or channel
        # self.issuemode - устанавливается ниже, поле определяет режим работы - дальнейшее действие по сообщению.
        # self.dirmode - устанавливается в _check_dir()
        self.issuenum = None    # номер задачи из истории, если есть, int
        self.rd = None          # redmine descriptor
        self.issue = None       # issue descriptor
        self.nightevent = False # по умолчанию событие не ночное
        self.eventdatetime = "" # по умолчанию значение для даты/времени старта события
        # вычисляем режим работы
        self._calculate_pmodetype()
        if self._check_create_dir(): # проверка доступности каталога, попытка создания, вычисление dirmode
            if self._read_file():    # проверка наличия файла для event_id, и сразу его чтение в issuenum
                self.issuemode = self._calc_issuemode(M_DOWN_APPEND,M_UP_APPEND)  # для DOWN-UP, файл истории есть
            else:
                self.issuemode = self._calc_issuemode(M_DOWN_NEW,M_PASS)          # файла истории нет
        else:
            self.issuemode = self._calc_issuemode(M_DOWN_NEW_NODIR,M_PASS)  # каталог истории нам недоступен
        self.logger.info("issue.__init__: issuemode:{0},issuenum:{1},dirmode:{2},pmode:{3},ptype:{4}".format(
                            self.issuemode,self.issuenum, self.dirmode, self.pmode, self.ptype))

    def __str__(self):
        str = "Object:{5}, Filename:{0}, pmode:{1}, dirmode:{2}, issuemode:{3}, issuenum:{4}".format(
            self.filename, self.pmode, self.dirmode, self.issuemode, self.issuenum, type(self))
        return str

    def _calculate_pmodetype(self):
        # Вычисляем вспомогательные параметры pmode и ptype
        self.logger.debug("issue._calculate_pmodetype started")
        parameters = self.parameters
        message_type = parameters.get("message_type","not found")
        if (message_type == "ChannelUP"):
            ptype,pmode=P_CHANNEL,P_UP
        elif (message_type == "OfficeUP"):
            ptype,pmode=P_OFFICE,P_UP
        elif (message_type == "ChannelDOWN"):
            ptype,pmode=P_CHANNEL,P_DOWN
        elif (message_type == "OfficeDOWN"):
            ptype,pmode=P_OFFICE,P_DOWN
        else:
            raise ArgvError("def _calculate_pmodetype: Critical error, message_type={0}".format(message_type))
        self.pmode = pmode
        self.ptype = ptype
        return True

    def _calc_issuemode(self,issuemode_for_down,issuemode_for_up):
        # Для удобства и понятности кода
        return issuemode_for_down if self.pmode == P_DOWN else issuemode_for_up

    def _calculate_nightevent(self):
        def _between_21_6(hour):
            return True if (hour>21) or (hour<6) else False
        logger = self.logger
        logger.debug("issue._calculate_nightevent started")
        parameters = self.parameters
        options = self.options
        issuedatetime = self.issuedatetime
        date_format = options["date_format"]
        startdatetime = datetime.datetime.strptime(issuedatetime,date_format)
        recoverydatetime = datetime.datetime.strptime(parameters["event_recovery_datetime"],date_format)
        # =True, если часы в self.issuedatetime и self.parameters["event_recovery_datetime"] одновременно <5
        # и >22, а также self.parameters["age"] <8
        if _between_21_6(startdatetime.hour) and _between_21_6(recoverydatetime.hour) and self.age<8:
            self.nightevent=True
        logger.debug("issue._calculate_nightevent: nightevent={0}".format(self.nightevent))

    def _check_create_dir(self):
        # Проверяем доступ к каталогу, пытаемся его создать, формируем dirmode
        # print("test_check_dir tmpdir: {0}".format(self.tmpdir))
        self.logger.debug("issue._check_create_dir started")
        tmpdir = self.tmpdir
        if not os.access(tmpdir, os.F_OK):
            try:
                os.mkdir(tmpdir, 0o744)
                self.dirmode = 0
                self.logger.debug("issue._check_dir: tmpdir={0} creating was successfull.".format(tmpdir))
                return True
            except (IOError, OSError):
                self.dirmode = 1  # errorcode=1 - невозможно создать каталог, каталог недоступен
                self.logger.error("issue._check_dir: tmpdir={0} creating error.".format(tmpdir))
                return False
        else:
            self.dirmode = 0
            self.logger.debug("issue._check_dir: tmpdir={0} access was successfull.".format(tmpdir))
            return True

    def _read_file(self):
        # читает файл, заполняет issuenum, возвращает успех/неуспех
        logger = self.logger
        logger.debug("issue._read_file started")
        try:
            fd = open(self.filename, mode="r")
            line1 = fd.readline().strip()
            line2 = fd.readline().strip()
            self.issuenum = int(line1)
            self.issuedatetime = line2
            logger.info("issue._read_file: file {0} read success. Line1={1}, Line2={2}".format(self.filename,
                                                                                               line1,line2))
            return True
        except (IOError, OSError, ValueError) as err:
            self.issuenum = None
            logger.info("issue._read_file: file={0} read or int conversion unsuccessfull: {1}".format(self.filename,
                                                                                                      str(err)))
            self._delete_file(False)
            return False

    def _delete_file(self, log=True):
        # Удаляем файл issue. Если log=True - то при ошибке пишем лог,
        #       иначе - не пишем (для случая, когда файл был, а задачи не было - попытка удаления)
        logger = self.logger
        logger.debug("issue._delete_file started")
        try:
            os.unlink(self.filename)
            logger.info("issue._delete_file: File {0} deletion was successfull".format(self.filename))
            return True
        except (IOError, OSError):
            if log:
                logger.error("issue._delete_file: File {0} didnt delete".format(self.filename))
            return False

    def _write_file(self):
        # Создаем заново issue файл, пишем в issue файл номер issue. Номер берется из переменной  класса.
        logger = self.logger
        logger.debug("issue._write_file started")
        if not self.dirmode:
            try:
                fd = open(self.filename, "w")
                fd.write(str(self.issuenum)+"\n")
                fd.write(self.issuedatetime)
                fd.close()
                logger.info(" issue._write_file. File={0} wrote success, issuenum={1}, issue_datetime={2}".format(
                            self.filename,self.issuenum,self.issuedatetime))
                return True
            except (IOError, OSError) as err:
                logger.error("issue._write_file: File={0} creation error.".format(self.filename))
                return False
        else:
            logger.error("issue._write_file: Attempt to write file {0} with dircode=1".format(self.filename))
            return False

    def _redmine_connect(self):
    #   Задаем формат даты, не проверям сертификат сервера на валидность, возвращаем redmine дескриптор
        self.logger.debug("issue._redmine_connect started")
        if not self.rd:
            server = self.parameters.get("server")
            key = self.parameters.get("key")
            self.rd = redmine.Redmine(server, key=key, date_format='%Y.%m.%d', requests={'verify': False})
            self.logger.debug("issue._redmine_connect: rd={0} created".format(self.rd))
        return self.rd

    def _make_new_redmine_issue(self, createfile=True):
        # формируем структуру для создания новой задачи
        # создаем новую задачу
        # если успешно - записываем в файл номер новой задачи
        logger = self.logger
        logger.debug("issue._make_new_redmine_issue started")
        options = self.options
        rd = self._redmine_connect()
        parameters = self.parameters
        issue = rd.issue.new()
        issue.project_id = parameters["project_id"]
        issue.tracker_id = parameters["tracker_id"]
        issue.status_id = parameters["status_id"]
        issue.priority_id = parameters["priority_id"]
        issue.assigned_to_id = parameters["assigned_to_id"]
        issue.watcher_user_ids = parameters["watcher_user_ids"]
        issue.subject = self.subject
        issue.description = self.body
        #issue.parent_issue_id = 0
        #issue.start_date = date(2014, 1, 1)
        #issue.due_date = date(2014, 2, 1)
        #issue.estimated_hours = 4
        #issue.done_ratio = 40
        # issue.custom_fields =  [{'id': 1, 'value': 'foo'}, {'id': 2, 'value': 'bar'}]
        issue.custom_fields = parameters.get("custom_fields",[])
        #issue.uploads = [{'path': '/absolute/path/to/file'}, {'path': '/absolute/path/to/file2'}]
        try:
            issue.save()
            self.issuenum = issue.id
            logger.info("issue._make_new_redmine_issue: Issue {0} with event_id: {1[event_id]}"
                             " saved successfully".format(self.issuenum, parameters))

            if createfile:
               self._write_file()
        except redmine.exceptions.BaseRedmineError as err:
            logger.error("issue._make_new_redmine_issue: Issue creation error:{0}".format(err))
            raise
        return True

    def _get_issue_from_redmine(self):
        """
        Получает из redmine задачу по номеру issuenum
        """
        logger = self.logger
        logger.debug("issue._get_issue_from_redmine started")
        issuenum = self.issuenum
        try:
            self.issue = self._redmine_connect().issue.get(issuenum)
            self.logger.info("issue._get_issue_from_redmine: get of issue {0} was successfull".format(issuenum))
        except Exception as err:
            self.issue = None
            self.logger.error("issue._get_issue_from_redmine: error getting issue {0}. Error:{1}".format(issuenum,err))
        return self.issue

    def _update_redmine_issue(self):
        # формируем структуру для обновления,
        #       в т.ч приоритет 3 для канала, 5 для офиса, записываем обновление
        # для UP удаляем файл
        logger = self.logger
        logger.debug("issue._update_redmine_issue started")
        if self._get_issue_from_redmine():
            parameters = self.parameters
            # формируем описание для журнала задачи, формируемомго при обновлении в редмайне
            argarray=dict(notes = self.body)
            # для событий UP добавляем новые значения некоторых полей: custom_fields и стандартные поля
            if self.pmode == P_UP:
                argarray.update(custom_fields=parameters["custom_fields"])
                argarray.update(status_id=parameters["status_id"])
            try:
                logger.info("issue._update_redmine_issue: argarray={0}".format(argarray))
                self.rd.issue.update(self.issuenum,**argarray)
                logger.info("issue._update_redmine_issue: Update issue:{0} was successfull".format(self.issuenum))
            except Exception as err:
                logger.error("issue._update_redmine_issue:"
                             " Update issue:{0} was unsuccess, error:{1}".format(self.issuenum,err))
            # для cообщения типа UP удаляем файл
            if self.pmode == P_UP:
                self._delete_file(log=True)

    def _make_subject(self):
        # Формируем правильную тему для новой задачи. Задачи создаются и требуют темы только при DOWN сообщении
        logger = self.logger
        logger.debug("issue._make_subject started")
        subject="Default"
        parameters = self.parameters
        message_type = self.parameters["message_type"]
        try:
            if message_type=="OfficeDOWN":
                subject = self.options.get("Office_DOWN_subject_template","Офис DOWN").format(parameters)
            elif message_type=="ChannelDOWN":
                subject = self.options.get("Channel_DOWN_subject_template","Канал DOWN").format(parameters)
            logger.debug("issue._make_subject: subject: {0}".format(subject))
        except (ValueError, KeyError) as err:
            logger.error("issue._make_subject: error creating subject: {0}".format(err))
        return subject

    def _make_body(self):
        # Формируем правильный description для задачи
        logger = self.logger
        logger.debug("issue._make_body started")
        body=""
        parameters = self.parameters
        try:
            if self.ptype == P_OFFICE:
                if self.pmode == P_DOWN:
                    self.logger.debug("issue._make_body: use Office_DOWN_description_template")
                    body = self.options.get("Office_DOWN_description_template","Офис DOWN").format(parameters)
                elif self.pmode == P_UP:
                    self.logger.debug("issue._make_body: use Office_UP_description_template")
                    body = self.options.get("Office_UP_description_template","Офис UP").format(parameters)
            elif self.ptype == P_CHANNEL:
                if self.pmode == P_DOWN:
                    body = self.options.get("Channel_DOWN_description_template","Канал").format(parameters)
                elif self.pmode == P_UP:
                    body = self.options.get("Channel_UP_description_template","Канал").format(parameters)
            self.logger.debug("issue._make_body: body={0}".format(body))
        except (ValueError, KeyError) as err:
            self.logger.error("issue._make_body: error creating body, error={0}".format(err))
        return body

    def _calculate_hours_age(self):  #
        event_age = self.parameters["event_age"]
        self.logger.debug("issue._calculate_hours_age started, event_age={0}".format(event_age))
        age=float(0)
        mn = dict(d=24.0,h=1.0,m=1.0/60)
        for s in event_age.split():
            for char in mn.keys():
                try:
                    age+=float(s[0:s.index(char)])*mn[char]
                except: pass
        self.age = age
        age = "{0:.2f}".format(age).replace(".",",")
        self.parameters["event_age"] = age
        self.logger.debug("issue._calculate_hours_age: age={0}".format(age))
        return True

    def _prepare_parameters(self):
        """
        Проверяет параметры на наличие по списку полей для соответствующего message_type, одновременно формирует
        список словарей customfields.
        Для некоторых случаев (пока только ночные события) формирует и переопределяет некоторые поля
        Преобразует ряд полей в тип int.
        При ошибках - исключение ArgvError.
        """
        logger = self.logger
        logger.debug("issue._prepare_parameters started")
        parameters = self.parameters
        options = self.options
        if self.pmode == P_DOWN:
            self.subject = self._make_subject()
        self.body = self._make_body()
        found_fields = []
        missed_fields = []
        custom_fields=[]
        try:
            message_type = parameters["message_type"]
            intfields = options[message_type+"_int"].split()
            listfields = options[message_type+"_intlist"].split()
            custom_fields_dict = options["custom_fields"]
        except KeyError as err:
            raise ArgvError("def issue.prepare_parameters exception: options KeyError={0}.".format(err))
        fields = options[message_type].split()          # список полей, которые должны быть
        custom_fields_keys = custom_fields_dict.keys()  # список имен всех возможных кастомных полей
        # для событий UP формируем age и вычисляем признак ночного события
        if self.pmode == P_UP:
            self._calculate_hours_age()
            self._calculate_nightevent()
        # для события DONW пишем переменную для возможной записи файла
        if self.pmode == P_DOWN:
            self.issuedatetime = parameters.get("event_datetime")
        # для ночного события делаем дополнительное custom поле и переназначаем status_id
        if self.nightevent:
            parameters["status_id"] = parameters["night_status_id"]
            if self.ptype == P_OFFICE:
                parameters["office_reason"] = parameters["night_office_reason"]
                fields.append("office_reason")
            if self.ptype == P_CHANNEL:
                parameters["channel_reason"] = parameters["night_channel_reason"]
                fields.append("channel_reason")
        keys = parameters.keys()  # список полей в parameters
        # А тут проверяем поля на наличие и одновременно формируем список кастомных полей.
        for field in fields:
            if field not in keys:
                missed_fields.append(field)
            else:
                found_fields.append(field)
                if field in custom_fields_keys:
                    custom_fields.append(dict(id=custom_fields_dict[field],value=parameters[field]))
        parameters.update(custom_fields=custom_fields)
        logger.debug("issue._prepare_parameters: parameters={0}".format(parameters))
        if len(missed_fields) > 0:
            raise ArgvError("def issue._prepare_parameters exception: "
                            "Some fields not found: {0}. Found fields: {1}".format(missed_fields, found_fields))
        # приводим тип параметрам int
        logger.debug("issue._prepare_parameters: Start convert to int")
        try:
            for key in intfields:
                parameters[key] = int(parameters[key])
        except ValueError:
            raise ArgvError("def prepare_parameters: Field {0}={1} can't convert to int.".format(key,parameters[key]))
        # формируем параметры-списки целых
        try:
            for key in listfields:
                a=[]
                for s in parameters[key].strip().split(","):
                    if len(s.strip())>0:
                        a.append(int(s))
                parameters[key] = a
        except ValueError:
            raise ArgvError("def prepare_parameters: listfield {0}={1} "
                                    "can't convert to int's list.".format(key,parameters[key]))
        return True

    def process(self):
        issuemode = self.issuemode
        logger = self.logger
        if issuemode == M_DOWN_NEW:
            logger.debug("issue.process: start M_DOWN_NEW")
            self._prepare_parameters()
            self._make_new_redmine_issue()
        elif issuemode == M_DOWN_APPEND:
            logger.debug("issue.process: start M_DOWN_APPEND")
            self._prepare_parameters()
            self._update_redmine_issue()
        elif issuemode == M_UP_APPEND:
            logger.debug("issue.process: start M_UP_APPEND")
            self._prepare_parameters()
            self._update_redmine_issue()
        elif issuemode == M_DOWN_NEW_NODIR:
            logger.debug("issue.process: start M_DOWN_NEW_NODIR")
            self._prepare_parameters()
            self._make_new_redmine_issue(createfile=False)
        elif issuemode == M_UP_NODIR:
            logger.info("issue.process: For issuemode M_UP_NODIR select action PASS")
            pass
        elif issuemode == M_UP_NOFILE:
            logger.info("issue.process: For issuemode M_UP_NOFILE select action PASS")
            pass
        elif issuemode == M_PASS:
            logger.info("issue.process: For issuemode M_PASS select action PASS")
            pass
        else:
            raise Exception("def issue.process: exception, undefined issuemode={0}".format(issuemode))
        return True

def prepare_args(args, logger):
    """
    Получаем аргументы в args, разбираем аргументы,
    формируем словарь аргументов. Проверяем наличие базовых параметров message_type, event_id,
    [office_id, channel_id].

    При ошибке - генерация исключения.
    Exceptions: ArgvError
    return: dict of parameters
    """
    # если передано не 4 аргумента - генерируем исключение, иначе пишем для удобства аргументы в переменные
    logger.debug("def prepare_args started")
    logger.debug("def prepare_args: command line arguments: {0}".format(args))
    if len(args) == 4:
        to, subject, body = args[1], args[2], args[3]
    else:
        error = "def prepare_args: len(args)!=4"
        raise ArgvError(error)
    # тут будем собирать параметры
    parameters = {}
    # анализируем переменную to. Если to=="kspd-tracker", берем серкер и ключ из настроек скрипта
    try:
        if to == "kspd-tracker":
            parameters.update(server=OPTIONS["server"], key=OPTIONS["key"])
        else:
            a, b = to.strip().rsplit(":",1)  # may be ValueError!!
            parameters.update(server=a.strip(), key=b.strip())
        # prepare Subject
        message_type = subject.strip()
        parameters.update(message_type=message_type)
        # Prepare Body
        for line in body.strip().split("\n"):
            a, b = line.strip().split(":",1)  # may be ValueError!!
            parameters.update([(a.strip(), b.strip())])
        if message_type in ("ChannelDOWN", "ChannelUP"):
            logger.info("Prepare_args passed. message_type: {0[0]}, channel_id: {0[1]}, event_id: {0[2]} ".format(
                [parameters[key] for key in "message_type channel_id event_id".split()]))
        elif message_type in ("OfficeDOWN", "OfficeUP"):
            logger.info("Prepare_args passed. message_type: {0[0]}, office_id: {0[1]}, event_id: {0[2]} ".format(
                [parameters[key] for key in "message_type office_id event_id".split()]))
        else:
            error = "def prepare_args: critical error, message_type={0} incorrect".format(message_type)
            raise ArgvError(error)
        logger.debug("def prepare_args: parameters dict: {0}".format(parameters))
    except (ValueError, KeyError) as err:
        error = "def prepare_args: critical ValueError or KeyError: {0}".format(err)
        raise ArgvError(error)
    return parameters

def start_logger(options, printerror = False):
    """ Инициализирует логгер из модуля logging.

    Берет переменные для настройки из options: logname, logdir (dir or severity), loghandler. loglevel, logformat.
    В настоящее время умеет работать c обработчиками
    SysLogHandler и FileHandler (по умолчанию).
    :return: ссылку на объект-логгер или None при ошибке
    """
    logname = options.get("logname", "root")
    logdir = options.get("logdir", "./log").replace("/", os.sep)
    handler = options.get("loghandler", "FileHandler")
    loglevel = getattr(logging, options.get("loglevel", logging.INFO))
    logger = logging.getLogger(logname)
    try:
        logger.setLevel(loglevel)  # may be AttributeError
        # create handler
        if handler == "FileHandler":
            logformat = options.get("logformat", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            fhname = "{0}{1}{2}_{3}_{4}.log".format(logdir, os.sep, logname, int(time.time()), os.getpid())
            lh = logging.FileHandler(fhname)
        elif handler == "SysLogHandler":
            logformat = options.get("logformat", "%(process)d - %(levelname)s - %(message)s")
            lh = logging.handlers.SysLogHandler(
                facility=getattr(logging.handlers.SysLogHandler, options.get("facility","LOG_LOCAL4")),
                address = options.get("syslogdir","/dev/log")
            )
        if options["log2console"]:
            console_lh = logging.StreamHandler()
        # create formatter and add it to the handler
        formatter = logging.Formatter(logformat)
        lh.setFormatter(formatter)
        if options["log2console"]:
            formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
            console_lh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(lh)
        if options["log2console"]:
            logger.addHandler(console_lh)
        logger.debug("Logger init success, name:{0}, handler:{1}, dir(severity):{2}".format(logname, handler, logdir))
    except Exception as err:
        if printerror: print ("logger init error")
        return None
    return logger

def main():
    # create logger
    logger = start_logger(OPTIONS, printerror = True)
    if not logger: sys.exit(1)
    # в args присваиваем список параметров для целей тестирования или sys.argv для боевого скрипта

    #args = testargs.testargs_ChannelDOWN
    #args = testargs.testargs_ChannelUP
    #args = testargs.testargs_ChannelDOWNnight
    #args = testargs.testargs_ChannelUPnight

    #args = testargs.testargs_OfficeDOWN
    #args = testargs.testargs_OfficeUP
    #args = testargs.testargs_OfficeDOWNnight
    #args = testargs.testargs_OfficeUPnight

    args = sys.argv

    try:
        parameters = prepare_args(args,logger)
        issue = Issue(parameters, OPTIONS, logger)
        issue.process()
    except ArgvError as err:
        logger.critical(err)
        sys.exit(1)

if __name__ == "__main__":
    main()

