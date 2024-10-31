# Added from https://github.com/MehmedGIT/OtoN_Converter/tree/master
from .models import NextflowFileExecutable
from .validators.ocrd_validator import OCRDValidator


class Converter:
    def __init__(self):
        pass

    @staticmethod
    def convert_OtoN(input_path: str, output_path: str, dockerized: bool = False):
        validator = OCRDValidator()
        validator.validate(input_path)

        nf_file_executable = NextflowFileExecutable()
        nf_file_executable.build_parameters(dockerized)
        # TODO: first_file_grps replacement is a wacky hack
        #  to replace the default value of the pre-built REPR_INPUT_FILE_GRP
        nf_processes, first_file_grps = nf_file_executable.build_nextflow_processes(validator.processors, dockerized)
        # TODO: This index is currently 3, but may change!
        nf_file_executable.nf_lines_parameters[3] = nf_file_executable.nf_lines_parameters[3].replace("null", f"{first_file_grps}")
        nf_file_executable.build_main_workflow(nf_processes)
        nf_file_executable.produce_nextflow_file(output_path)
