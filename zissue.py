#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# sys.argv[1] - To - URL:redmine API key, or "kspd-tracker"
# sys.argv[2] - Subject - [ChannelDOWN|ChannelUP|OfficeDOWN|OfficeUP]
# sys.argv[3] - Body - set of lines
#
# 1) Channel DOWN message, Subject -> message_type = ChannelDOWN
# project_id: 2         2-Test, 1-incidents
# tracker_id: 6         5-office, 6-channel
# status_id: 1          1-Новая
# priority_id: 2        2-
# assigned_to_id: 6     6-Отдел поддержки сети
# watcher_user_ids:     нет
# channel_id: {INVENTORY.SITE.ZIP}
# bank: {INVENTORY.SITE.ADDRESS.A}
# office: {INVENTORY.SITE.ADDRESS.B}
# event_id: {EVENT.ID}
# hub: {INVENTORY.SITE.ADDRESS.C}
# channel_type: {INVENTORY.SITE.NOTES}
# event_date: {EVENT.DATE}
# event_time: {EVENT.TIME}
# office_comments:  {INVENTORY.POC.PRIMARY.NOTES}
# fields = "message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
# "channel_id bank office event_id hub channel_type event_date event_time office_comments"
#
# 2) Channel UP message, Subject -> message_type = ChannelUP
# event_id: {EVENT.ID}
# channel_id: {INVENTORY.SITE.ZIP}
# event_recovery_date: {EVENT.RECOVERY.DATE}
# event_recovery_type: {EVENT.RECOVERY.TIME}
# event_age: {EVENT.AGE}
# status_id: 6          6-Автоматически решена
# night_status_id: 5
# night_reason: В нерабочее время
# fields = "message_type channel_id event_id event_recovery_date event_recovery_time event_age status_id
#           night_status_id, night_reason"
#
# 3) Office DOWN message, Subject -> message_type = OfficeDOWN
# project_id: 2         2-Test, 1-incidents
# tracker_id: 5         5-office, 6-channel
# status_id: 1          1-Новая
# priority_id: 4        2-
# assigned_to_id: 6     6-Отдел поддержки сети
# watcher_user_ids:     пусто
# office_id: {INVENTORY.SITE.ZIP}
# bank: {INVENTORY.SITE.ADDRESS.A}
# office: {INVENTORY.SITE.ADDRESS.B}
# event_id: {EVENT.ID}
# event_date: {EVENT.DATE}
# event_time: {EVENT.TIME}
# office_comments:  {INVENTORY.POC.PRIMARY.NOTES}
# fields = "message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
# "office_id bank office event_id event_date event_time office_comments"
#
# 4) Office UP message, Subject -> message_type = OfficeUP
# event_id: {EVENT.ID}
# office_id: {INVENTORY.SITE.ZIP}
# event_recovery_date: {EVENT.RECOVERY.DATE}
# event_recovery_type: {EVENT.RECOVERY.TIME}
# event_age: {EVENT.AGE}
# status_id: 6          6-Автоматически решена
# night_status_id: 5
# night_reason: В нерабочее время
# fields = "message_type office_id event_id event_recovery_date event_recovery_time event_age status_id
#           night_status_id, night_reason"
#
# Other redmine fields
# subject (string) – (required). Issue subject.
#    description (string) – (optional). Issue description.
#    start_date (string or date object) – (optional). Issue start date.
#    due_date (string or date object) – (optional). Issue end date.
#    custom_fields
#
import redmine
import logging
import sys
import os
import time
import testargs

OPTIONS = dict(
    log2console = True,          # True for test purposes
    loghandler="FileHandler",  # Обработчик логов, FileHandler or SysLogHandler,
    logdir="C:/Amv/Temp/zissue/log",  # Каталог для логфайлов или facility для SysLogHandler
    logname="zissue",  # logger name, filename for FileHandler
    tmpdir="C:/Amv/Temp/zissue/temp",  # Каталог временных файлов
    loglevel="DEBUG",  # Уровень логирования
    archivelog=False,  # Архивирование логфайлов после ? нереализовано, требует доработки...
    server="http://kspd-tracker.life.corp",
    key="1b2fb6be316492751a29bf119a1b2f9ca108ad49",
    ChannelDOWN="message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
                "channel_id bank office event_id hub channel_type event_datetime office_comments",
    ChannelDOWN_int="project_id tracker_id status_id priority_id assigned_to_id",
    ChannelDOWN_intlist="watcher_user_ids",
    ChannelUP="message_type channel_id event_id event_recovery_datetime event_age night_status_id night_reason",
    ChannelUP_int="",
    ChannelUP_intlist="",
    OfficeDOWN="message_type project_id tracker_id status_id priority_id assigned_to_id watcher_user_ids "
               "office_id bank office event_id event_datetime office_comments",
    OfficeDOWN_int="project_id tracker_id status_id priority_id assigned_to_id",
    OfficeDOWN_intlist="watcher_user_ids",
    OfficeUP="message_type office_id event_id event_recovery_datetime event_age night_status_id night_reason",
    OfficeUP_int="",
    OfficeUP_intlist="",
    custom_fields = dict(channel_id=10,bank=2,office=1,event_id=9,hub=12,
                         channel_type=11,office_comments=23,event_datetime=7,event_recovery_datetime=8,
                         event_age=6, reason=4),
    Office_DOWN_subject_template = "Zabbix: Офис {0[bank]} {0[office]} {0[office_id]} DOWN",
    Office_DOWN_description_template =
                            "Zabbix: Офис {0[bank]} {0[office]} {0[office_id]} DOWN, event_id: {0[event_id]}\n"
                            "Event started at {0[event_datetime]}",
    Office_UP_description_template = "Zabbix: Офис {0[office_id]} UP, event_id: {0[event_id]}",
    Channel_DOWN_subject_template = "Zabbix: Канал {0[bank]} {0[office]} {0[channel_id]} DOWN",
    Channel_DOWN_description_template =
                            "Zabbix: Канал {0[bank]} {0[office]} {0[channel_id]} DOWN, event_id: {0[event_id]}\n"
                            "Event started at {0[event_datetime]}",
    Channel_UP_description_template = "Zabbix: Канал {0[channel_id]} UP, event_id: {0[event_id]}",
    date_format = "%Y.%m.%d %H:%M:%S"       # скорее всего не нужен
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
        Инициализация класса: проверка каталога, вычисление issuemode и issuenum, другие вспомогательнеы элементы
        """
        logger.debug("issue.__init__ started")
        self.parameters = parameters
        self.options = options
        self.logger = logger
        self.tmpdir = self.options["tmpdir"].replace("/", os.sep)
        self.filename = self.tmpdir + os.sep + parameters["event_id"]
        self._calculate_pmodetype()
        # self.pmode,  DOWN или UP,
        # self.ptype,  office or channel
        # self.issuemode - устанавливается ниже
        # self.dirmode - устанавливается в _check_dir()
        self.issuenum = None    # номер задачи из истории, если есть, int
        self.rd = None          # redmine descriptor

        if self._check_create_dir(): # проверка доступности каталога, попытка создания, вычисление dirmode
            if self._read_file():    # проверка наличия файла для event_id, и сразу его чтение в issuenum
                self.issuemode = self._calc_issuemode(M_DOWN_APPEND,M_UP_APPEND)  # для DOWN-UP, файл истории есть
            else:
                self.issuemode = self._calc_issuemode(M_DOWN_NEW,M_PASS)          # файла истории нет
        else:
            self.issuemode = self._calc_issuemode(M_DOWN_NEW_NODIR,M_PASS)  # каталог истории нам недоступен
        self.logger.info("issue.__init__: issuemode:{0},issuenum:{1},dirmode:{2},pmode:{3},ptype:{4}".format(
                            self.issuemode,self.issuenum, self.dirmode, self.pmode, self.ptype))
        if self.pmode == P_DOWN:
            self.subject = self._make_subject()
        self.body = self._make_body()
        logger.debug("issue.__init__: before _prepare_parameters")
        self._prepare_parameters()

    def _calc_issuemode(self,issuemode_for_down,issuemode_for_up):
        return issuemode_for_down if self.pmode == P_DOWN else issuemode_for_up

    def _read_file(self):
        # читает файл, заполняет issuenum, возвращает успех/неуспех
        logger = self.logger
        logger.debug("issue._read_file started")
        try:
            fd = open(self.filename, mode="r")
            line = fd.readline()
            self.issuenum = int(line)
            logger.info("issue._read_file: file {0} read success. Line 1: {1}".format(self.filename, line))
            return True
        except (IOError, OSError, ValueError) as err:
            self.issuenum = None
            logger.info("issue._read_file: file={0} read or int conversion unsuccessfull: {1}".format(self.filename,str(err)))
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

    def _check_create_dir(self):
        # Проверяем доступ к каталогу, пытаемся его создать, формируем dirmode
        # print("test_check_dir tmpdir: {0}".format(self.tmpdir))
        self.logger.debug("issue._check_create_dir started")
        tmpdir = self.tmpdir
        if not os.access(tmpdir, os.F_OK):
            try:
                os.mkdir(tmpdir, mode=0o700)
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

    def _write_file(self):
        # Создаем заново issue файл, пишем в issue файл номер issue. Номер берется из переменной  класса.
        logger = self.logger
        logger.debug("issue._write_file started")
        if not self.dirmode:
            try:
                fd = open(self.filename, "w")
                fd.write(str(self.issuenum))
                fd.close()
                logger.info(" issue._write_file. File={0} wrote success, issuenum:{1}".format(self.filename,
                                                                                                   self.issuenum))
                return True
            except (IOError, OSError) as err:
                logger.error("issue._write_file: File={0} creation error.".format(self.filename))
                return False
        else:
            logger.error("issue._write_file: Attempt to write file {0} with dircode=1".format(self.filename))
            return False

    def __str__(self):
        str = "Object:{5}, Filename:{0}, pmode:{1}, dirmode:{2}, issuemode:{3}, issuenum:{4}".format(
            self.filename, self.pmode, self.dirmode, self.issuemode, self.issuenum, type(self))
        return str

    def _redmine_connect(self):
    #   Задаем формат даты, не проверям сертификат сервера на валидность, возвращаем redmine дескриптор
        self.logger.debug("issue._redmine_connect started")
        if not self.rd:
            server = self.parameters.get("server")
            key = self.parameters.get("key")
            self.rd = redmine.Redmine(server, key=key, date_format='%Y.%m.%d', requests={'verify': False})
            self.logger.debug("issue._redmine_connect: rd={0} created".format(self.rd))
        return self.rd

    def _get_issue_from_redmine(self):
        """
        Получает из redmine задачу по номеру issuenum
        """
        logger = self.logger
        logger.debug("issue._get_issue_from_redmine started")
        try:
            self.issue = self._redmine_connect().issue.get(self.issuenum)
            self.logger.info("issue._get_issue_from_redmine: get of issue {0} was successfull".format(self.issuenum))
        except Exception as err:
            self.logger.error("issue._get_issue_from_redmine: Error getting issue {0}. Error:{1}".format(self.issuenum,
                              err))
            self.issue = None
        return self.issue

    def _update_redmine_issue(self):
        # формируем структуру для обновления,
        #       в т.ч приоритет 3 для канала, 5 для офиса, записываем обновление
        # для UP удаляем файл
        logger = self.logger
        logger.debug("issue._update_redmine_issue started")
        argarray=dict(notes = self.body)
        if self.pmode == P_UP:
            argarray.update(custom_fields=self.parameters["custom_fields"])
        try:
            self.rd.issue.update(self.issuenum,**argarray)
            logger.info("issue._update_redmine_issue: Update issue:{0} was successfull")
        except Exception as err:
            logger.error("issue._update_redmine_issue: Update issue:{0} was unsuccess, error:{1}".format(self.issuenum,
                                                                                                         err))
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

    def _make_new_redmine_issue(self, createfile=True):
        # формируем структуру для создания новой задачи
        # создаем новую задачу
        # если успешно - записываем в файл номер новой задачи
        logger = self.logger
        logger.debug("issue._make_new_redmine_issue")
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
        except Exception as err:
            logger.error("issue._make_new_redmine_issue: Issue creation error:{0}".format(err))
        return True

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

    def _calculate_hours_age(self):  #
        self.logger.debug("issue._calculate_hours_age started")
        age=0
        mn = dict(d=24,h=1,m=1/60)
        for s in self.parameters["event_age"].split():
            for char in mn.keys():
                try:
                    age+=float(s[0:s.index(char)])*mn[char]
                except: pass
        age = str(age).replace(".",",")
        self.parameters["event_age"] = age
        self.logger.debug("issue._calculate_hours_age: age={0}".format(age))
        return True

    def _prepare_parameters(self):
        """
        Проверяет параметры на наличие по списку полей для соответствующего message_type, одновременно формирует
        список словарей customfields.
        Преобразует ряд полей в тип int.
        При ошибках - исключение ArgvError.
        """
        logger = self.logger
        logger.debug("issue._prepare_parameters started")
        parameters = self.parameters
        options = self.options
        keys = parameters.keys()
        found_fields = []
        missed_fields = []
        custom_fields=[]
        try:
            message_type = parameters["message_type"]
            intfields = options[message_type+"_int"].split()
            listfields = options[message_type+"_intlist"].split()
            custom_fields_dict = options["custom_fields"]
        except KeyError as err:
            raise ArgvError("def prepare_parameters exception: options KeyError={0}.".format(err))
        fields = options[message_type].split()
        custom_fields_keys = custom_fields_dict.keys()
        # для событий UP формируем age
        if self.pmode == P_UP:
            self._calculate_hours_age()
        # А тут проверяем поля на наличие и одновременно формируем список кастомных полей.
        for field in fields:
            if field not in keys:
                missed_fields.append(field)
            else:
                found_fields.append(field)
                if field in custom_fields_keys:
                    custom_fields.append(dict(id=custom_fields_dict[field],value=parameters[field]))
        parameters.update(custom_fields=custom_fields)
        logger.debug("issue._prepare_parameters: custom_fields={0}".format(self.parameters["custom_fields"]))
        if len(missed_fields) > 0:
            raise ArgvError("def prepare_parameters exception: Some fields not found: {0}. Found fields: {1}".format(
                            missed_fields, found_fields))
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
            self._make_new_redmine_issue()
        elif issuemode == M_DOWN_APPEND:
            logger.debug("issue.process: start M_DOWN_APPEND")
            if self._get_issue_from_redmine():
                self._update_redmine_issue()
        elif issuemode == M_UP_APPEND:
            logger.debug("issue.process: start M_UP_APPEND")
            if self._get_issue_from_redmine():
                self._update_redmine_issue()
        elif issuemode == M_DOWN_NEW_NODIR:
            logger.debug("issue.process: start M_DOWN_NEW_NODIR")
            self._make_new_redmine_issue(createfile=False)
        elif issuemode == M_UP_NODIR:
            logger.info("issue.process: For issuemode M_UP_NODIR select action PASS")
            pass
        elif issuemode == M_UP_NOFILE:
            logger.info("issue.process: For issuemode M_UP_NOFILE select action PASS")
            pass
        elif issuemode == M_PASS:
            logger.info("issue.process: For issuemode M_PASS select action PASS")
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
        logger.critical(error)
        raise ArgvError(error)
    # тут будем собирать параметры
    parameters = {}
    # анализируем переменную to. Если to=="kspd-tracker", берем серкер и ключ из настроек скрипта
    try:
        if to == "kspd-tracker":
            parameters.update(server=OPTIONS["server"], key=OPTIONS["key"])
        else:
            a, b = to.strip().rsplit(":", maxsplit=1)  # may be ValueError!!
            parameters.update(server=a.strip(), key=b.strip())
        # prepare Subject
        message_type = subject.strip()
        parameters.update(message_type=message_type)
        # Prepare Body
        for line in body.strip().split("\n"):
            a, b = line.strip().split(":", maxsplit=1)  # may be ValueError!!
            parameters.update([(a.strip(), b.strip())])
        if message_type in ("ChannelDOWN", "ChannelUP"):
            logger.info("Prepare_args passed. message_type: {0[0]}, channel_id: {0[1]}, event_id: {0[2]} ".format(
                [parameters[key] for key in "message_type channel_id event_id".split()]))
        elif message_type in ("OfficeDOWN", "OfficeUP"):
            logger.info("Prepare_args passed. message_type: {0[0]}, office_id: {0[1]}, event_id: {0[2]} ".format(
                [parameters[key] for key in "message_type office_id event_id".split()]))
        else:
            error = "def prepare_args: critical error, message_type={0} incorrect".format(message_type)
            logger.critical(error)
            raise ArgvError(error)
        logger.debug("def prepare_args: parameters dict: {0}".format(parameters))
    except (ValueError, KeyError) as err:
        error = "def prepare_args: critical ValueError or KeyError: {0}".format(err)
        logger.critical(error)
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
    logformat = options.get("logformat", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(logname)
    try:
        logger.setLevel(loglevel)  # may be AttributeError
        # create handler
        if handler == "FileHandler":
            fhname = "{0}{1}{2}_{3}_{4}.log".format(logdir, os.sep, logname, int(time.time()), os.getpid())
            lh = logging.FileHandler(fhname)
        elif handler == "SysLogHandler":
            lh = logging.SysLogHandler(facility=getattr(logging.SysLogHandler, logdir))
        if options["log2console"]:
            console_lh = logging.StreamHandler()
        # create formatter and add it to the handlers
        formatter = logging.Formatter(logformat)
        lh.setFormatter(formatter)
        if options["log2console"]:
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
    args = testargs.testargs_OfficeUP
    try:
        parameters = prepare_args(args,logger)
        issue = Issue(parameters, OPTIONS, logger)
        issue.process()
    except ArgvError as err:
        logger.critical(err)
        sys.exit(1)

if __name__ == "__main__":
    main()
