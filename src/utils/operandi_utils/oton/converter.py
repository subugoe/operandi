from operandi_utils.oton.nf_file_executable import NextflowFileExecutable
from operandi_utils.oton.validator import OCRDValidator


class OTONConverter:
    def __init__(self):
        self.ocrd_validator = OCRDValidator()

    def convert_oton_env_local(self, input_path: str, output_path: str):
        self.ocrd_validator.validate(input_path)
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)

        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters_local()
        # TODO: first_file_grps replacement is a wacky hack
        #  to replace the default value of the pre-built REPR_INPUT_FILE_GRP
        nf_processes, first_file_grps = nf_file_executable.build_nextflow_processes_local(
            ocrd_processor=list_processor_call_arguments)
        # TODO: This index is currently 3, but may change!
        nf_file_executable.nf_lines_parameters[3] = nf_file_executable.nf_lines_parameters[3].replace(
            "null", f"{first_file_grps}")
        nf_file_executable.build_main_workflow(nf_processes)
        nf_file_executable.produce_nextflow_file(output_path)

    def convert_oton_env_docker(self, input_path: str, output_path: str):
        self.ocrd_validator.validate(input_path)
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)

        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters_docker()
        # TODO: first_file_grps replacement is a wacky hack
        #  to replace the default value of the pre-built REPR_INPUT_FILE_GRP
        nf_processes, first_file_grps = nf_file_executable.build_nextflow_processes_docker(
            ocrd_processor=list_processor_call_arguments)
        # TODO: This index is currently 3, but may change!
        nf_file_executable.nf_lines_parameters[3] = nf_file_executable.nf_lines_parameters[3].replace(
            "null", f"{first_file_grps}")
        nf_file_executable.build_main_workflow(nf_processes)
        nf_file_executable.produce_nextflow_file(output_path)

    def convert_oton_env_apptainer(self, input_path: str, output_path: str):
        raise NotImplemented("This feature is not implemented yet!")
