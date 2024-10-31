from operandi_utils.oton.nf_file_executable import NextflowFileExecutable
from operandi_utils.oton.ocrd_validator import OCRDValidator


class OTONConverter:
    def __init__(self):
        self.ocrd_validator = OCRDValidator()

    def convert_oton_env_local(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        self.ocrd_validator.validate(input_path)
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)
        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters_local()
        nf_file_executable.build_nextflow_processes_local(ocrd_processor=list_processor_call_arguments)
        nf_file_executable.build_main_workflow()
        nf_file_executable.produce_nextflow_file(output_path)
        return nf_file_executable

    def convert_oton_env_docker(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        self.ocrd_validator.validate(input_path)
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)
        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters_docker()
        nf_file_executable.build_nextflow_processes_docker(ocrd_processor=list_processor_call_arguments)
        nf_file_executable.build_main_workflow()
        nf_file_executable.produce_nextflow_file(output_path)
        return nf_file_executable

    def convert_oton_env_apptainer(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        raise NotImplemented("This feature is not implemented yet!")
