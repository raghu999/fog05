import sys
import os
import uuid
import psutil
import json
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from NativeEntity import NativeEntity
from jinja2 import Environment
import time

class Native(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(Native, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from Native Plugin')
        self.HOME = str("runtime/%s/entity" % self.uuid)
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.BASE_DIR = "/opt/fos/native"
        self.LOG_DIR = "logs"
        self.STORE_DIR = "apps"

        self.startRuntime()

    def startRuntime(self):
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()', ' Native Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        if self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.STORE_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.STORE_DIR))
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.STORE_DIR))
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))

        return self.uuid

    def stopRuntime(self):
        self.agent.logger.info('stopRuntime()', ' Native Plugin - Destroy running BE')
        for k in list(self.current_entities.keys()):
            entity = self.current_entities.get(k)
            if entity.getState() == State.PAUSED:
                self.resumeEntity(k)
                self.stopEntity(k)
                self.cleanEntity(k)
                self.undefineEntity(k)
            if entity.getState() == State.RUNNING:
                self.stopEntity(k)
                self.cleanEntity(k)
                self.undefineEntity(k)
            if entity.getState() == State.CONFIGURED:
                self.cleanEntity(k)
                self.undefineEntity(k)
            if entity.getState() == State.DEFINED:
                self.undefineEntity(k)
        self.agent.logger.info('stopRuntime()', '[ DONE ] Native Plugin - Bye')
        return True

    def defineEntity(self, *args, **kwargs):

        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = str("%s/%s/native_%s.log" % (self.BASE_DIR,self.LOG_DIR, entity_uuid))
            entity = NativeEntity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('source'),
                                  kwargs.get('args'), out_file)
        else:
            return None

        self.agent.logger.info('defineEntity()', ' Native Plugin - Define BE')
        entity.setState(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('defineEntity()', ' Native Plugin - Defined BE uuid %s' % entity_uuid)
        return entity_uuid

    def undefineEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' Native Plugin - Undefine BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] Native Plugin - Undefine BE uuid %s' % entity_uuid)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' Native Plugin - Configure BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            self.agent.getOSPlugin().createFile(entity.outfile)
            if entity.source is not None:
                zip_name = entity.source.split('/')[-1]
                self.agent.getOSPlugin().createDir(str("%s/%s/%s") % (self.BASE_DIR, self.STORE_DIR, entity.name))
                wget_cmd = str('wget %s -O %s/%s/%s/%s' %
                               (entity.source, self.BASE_DIR, self.STORE_DIR, entity.name, zip_name))
                unzip_cmd = str("unzip %s/%s/%s/%s -d %s/%s/%s/" %
                                (self.BASE_DIR, self.STORE_DIR, entity.name, zip_name,
                                 self.BASE_DIR, self.STORE_DIR, entity.name))
                self.agent.getOSPlugin().executeCommand(wget_cmd, True)
                self.agent.getOSPlugin().executeCommand(unzip_cmd, True)

            entity.onConfigured()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "configured"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('configureEntity()', '[ DONE ] Native Plugin - Configure BE uuid %s' % entity_uuid)
            return True

    def cleanEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' Native Plugin - Clean BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            self.agent.getOSPlugin().removeFile(entity.outfile)
            if entity.source is not None:
                self.agent.getOSPlugin().removeDir("%s/%s/%s" % (self.BASE_DIR, self.STORE_DIR, entity.name))
            entity.onClean()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "cleaned"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('cleanEntity()', '[ DONE ] Native Plugin - Clean BE uuid %s' % entity_uuid)
            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' Native Plugin - Starting BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            if entity.source is None:
                cmd = str("%s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
            else:
                native_dir = str("%s/%s/%s" % (self.BASE_DIR, self.STORE_DIR, entity.name))
                pid_file = str("%s/%s/%s/%s" % (self.BASE_DIR, self.STORE_DIR, entity.name, entity_uuid))
                run_script = self.__generate_run_script(entity.command, native_dir, pid_file)
                self.agent.getOSPlugin().storeFile(run_script, native_dir, str("%s_run.sh" % entity_uuid))
                chmod_cmd = str("chmod +x %s/%s" % (native_dir, str("%s_run.sh" % entity_uuid)))
                self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
                cmd = str("%s/%s" % (native_dir, str("%s_run.sh" % entity_uuid)))

            process = self.__execute_command(cmd, entity.outfile)

            if entity.source is not None:
                time.sleep(1)
                pid_file = str("%s/%s/%s/%s.pid" % (self.BASE_DIR, self.STORE_DIR, entity.name, entity_uuid))
                pid = int(self.agent.getOSPlugin().readFile(pid_file))
                entity.onStart(pid, process)
            else:
                entity.onStart(process.pid, process)

            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('runEntity()', '[ DONE ] Native Plugin - Runnign BE uuid %s' % entity_uuid)
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' Native Plugin - Stop BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            p = entity.process
            p.terminate()
            if entity.source is not None:
                pid = entity.pid
                self.agent.getOSPlugin().sendSigKill(pid)

            entity.onStop()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "stop"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('stopEntity()', '[ DONE ] Native Plugin - Stopped BE uuid %s' % entity_uuid)
            return True

    def pauseEntity(self, entity_uuid):
        self.agent.logger.warning('pauseEntity()', 'Native Plugin - Cannot pause a BE')
        return False

    def resumeEntity(self, entity_uuid):
        self.agent.logger.warning('resumeEntity()', 'Native Plugin - Cannot resume a BE')
        return False

    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri,):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)

    def __execute_command(self, command, out_file):
        f = open(out_file, 'w')
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=f)
        return p

    def __generate_run_script(self, cmd, directory, outfile):
        template_xml = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'run_native.sh'))
        na_script = Environment().from_string(template_xml)
        na_script = na_script.render(command=cmd, path=directory,outfile=outfile)
        return na_script

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' Native Plugin - React to to URI: %s Value: %s Version: %s' %
                               (uri, value, v))
        if value is None and v is None:
            self.agent.logger.info('__react_to_cache()', ' Native Plugin - This is a remove for URI: %s' % uri)
            entity_uuid = uri.split('/')[-1]
            self.undefineEntity(entity_uuid)
        else:
            uuid = uri.split('/')[-1]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            react_func = self.__react(action)
            if react_func is not None and entity_data is None:
                react_func(uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': uuid})
                if action == 'define':
                    react_func(**entity_data)
                else:
                    react_func(entity_data)

    def __react(self, action):
        r = {
            'define': self.defineEntity,
            'configure': self.configureEntity,
            'clean': self.cleanEntity,
            'undefine': self.undefineEntity,
            'stop': self.stopEntity,
            'resume': self.resumeEntity,
            'run': self.runEntity
        }

        return r.get(action, None)





