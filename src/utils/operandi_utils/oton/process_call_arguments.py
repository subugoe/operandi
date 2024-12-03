from json import dumps as json_dumps
from logging import getLevelName, getLogger
from typing import Optional
from operandi_utils.oton.constants import (
    BS, CONST_DIR_IN, CONST_DIR_OUT, CONST_WORKSPACE_DIR, CONST_METS_PATH, CONST_PAGE_RANGE, CONST_METS_SOCKET_PATH,
    OCRD_ALL_JSON, OTON_LOG_LEVEL
)

# This class is based on ocrd.task_sequence.ProcessorTask
class ProcessorCallArguments:
    def __init__(
        self,
        executable: str,
        input_file_grps: Optional[str] = None,
        output_file_grps: Optional[str] = None,
        parameters: Optional[dict] = None,
        workspace_dir: str = None,
        mets_file_path: str = None,
        mets_socket_path: str = None,
        page_id: str = None
    ):
        if not executable:
            raise ValueError(f"Missing executable name")
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))

        self.executable = f'ocrd-{executable}'
        self.workspace_dir = workspace_dir
        self.mets_file_path = mets_file_path
        self.mets_socket_path = mets_socket_path
        self.input_file_grps = input_file_grps
        self.output_file_grps = output_file_grps
        self.page_id = page_id
        self.parameters = parameters if parameters else {}
        self.ocrd_tool_json = OCRD_ALL_JSON.get(self.executable, None)

    def dump_bash_form(self) -> str:
        dump = ''
        dump += f'{self.executable}'
        if self.mets_socket_path:
            dump += f' -U {self.mets_socket_path}'
        if self.workspace_dir:
            dump += f' -w {self.workspace_dir}'
        if self.mets_file_path:
            dump += f' -m {self.mets_file_path}'
        dump += f' -I {self.input_file_grps}'
        dump += f' -O {self.output_file_grps}'
        if self.page_id:
            dump += f' --page_id {self.page_id}'
        if self.parameters:
            dump += f" -p '{json_dumps(self.parameters)}'"
        return dump

    def dump_bash_form_with_placeholders(self):
        dump = ''
        dump += f'{self.executable}'
        if self.mets_socket_path:
            dump += f' -U ${BS[0]}{CONST_METS_SOCKET_PATH}{BS[1]}'
        dump += f' -w ${BS[0]}{CONST_WORKSPACE_DIR}{BS[1]}'
        dump += f' -m ${BS[0]}{CONST_METS_PATH}{BS[1]}'
        dump += f' --page-id ${BS[0]}{CONST_PAGE_RANGE}{BS[1]}'
        dump += f' -I ${BS[0]}{CONST_DIR_IN}{BS[1]}'
        dump += f' -O ${BS[0]}{CONST_DIR_OUT}{BS[1]}'
        if self.parameters:
            dump += f" -p '{json_dumps(self.parameters)}'"
        return dump

    def self_validate(self):
        if not self.ocrd_tool_json:
            self.logger.error(f"Ocrd tool JSON of '{self.executable}' not found!")
            raise ValueError(f"Ocrd tool JSON of '{self.executable}' not found!")
        if not self.input_file_grps:
            self.logger.error(f"Processor '{self.executable}' requires 'input_file_grp' but none was provided.")
            raise ValueError(f"Processor '{self.executable}' requires 'input_file_grp' but none was provided.")
        if 'output_file_grp' in self.ocrd_tool_json and not self.output_file_grps:
            self.logger.error(f"Processor '{self.executable}' requires 'output_file_grp' but none was provided.")
            raise ValueError(f"Processor '{self.executable}' requires 'output_file_grp' but none was provided.")
