from operandi_utils.oton.nf_file_executable import NextflowFileExecutable
from operandi_utils.oton.ocrd_validator import OCRDValidator


class OTONConverter:
    def __init__(self):
        self.ocrd_validator = OCRDValidator()

    def convert_oton(
        self,
        input_path: str,
        output_path: str,
        environment: str = "apptainer",
        with_mets_server: bool = True
    ):
        list_processor_call_arguments = self.ocrd_validator.validate(input_path)
        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters(environment=environment, with_mets_server=with_mets_server)
        nf_file_executable.build_nextflow_processes(
            ocrd_processors=list_processor_call_arguments, environment=environment, with_mets_server=with_mets_server)
        nf_file_executable.build_main_workflow(with_mets_server=with_mets_server)
        nf_file_executable.produce_nextflow_file(output_path, with_mets_server)
        return nf_file_executable
