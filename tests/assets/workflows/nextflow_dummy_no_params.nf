nextflow.enable.dsl = 2

params.workspace = ""
params.mets = ""
params.input_group = ""

process ocrd_dummy {
	maxForks 1

	input:
		path mets_file
		val input_dir
		val output_dir

	output:
		val output_dir

	script:
	"""
	ocrd-dummy -I ${input_dir} -O ${output_dir}
	"""
}

workflow {
	main:
		ocrd_dummy(params.mets, params.input_group, "OCR-D-DUMMY")
}

