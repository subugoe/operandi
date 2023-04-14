nextflow.enable.dsl = 2

params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.input_group = "OCR-D-IMG"

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

