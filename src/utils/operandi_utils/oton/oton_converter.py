from operandi_utils.oton.nf_file_executable import NextflowFileExecutable
from operandi_utils.oton.ocrd_validator import OCRDValidator


class OTONConverter:
    def __init__(self):
        self.ocrd_validator = OCRDValidator()

    def __convert_oton(self, input_path: str, output_path: str, environment: str):
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)
        nf_file_executable = NextflowFileExecutable()
        if environment == "local":
            nf_file_executable.build_parameters_local()
            nf_file_executable.build_nextflow_processes_local(ocrd_processor=list_processor_call_arguments)
        elif environment == "docker":
            nf_file_executable.build_parameters_docker()
            nf_file_executable.build_nextflow_processes_docker(ocrd_processor=list_processor_call_arguments)
        elif environment == "apptainer":
            nf_file_executable.build_parameters_apptainer()
            nf_file_executable.build_nextflow_processes_apptainer(ocrd_processor=list_processor_call_arguments)
        nf_file_executable.build_main_workflow()
        nf_file_executable.produce_nextflow_file(output_path)
        return nf_file_executable

    def convert_oton_env_local(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        return self.__convert_oton(input_path, output_path, environment="local")

    def convert_oton_env_docker(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        return self.__convert_oton(input_path, output_path, environment="docker")

    def convert_oton_env_apptainer(self, input_path: str, output_path: str) -> NextflowFileExecutable:
        return self.__convert_oton(input_path, output_path, environment="apptainer")
