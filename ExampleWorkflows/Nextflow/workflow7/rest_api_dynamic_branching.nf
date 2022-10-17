import groovy.json.JsonSlurper
nextflow.enable.dsl = 2

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 7 - EXPERIMENTAL
         ===========================================
         """
         .stripIndent()

// Get json that has timestamp
def rest_api_get(){
  def connection = new URL("http://operandi.ocr-d.de:8000/").openConnection()
  def response_code = connection.getResponseCode();
  println("Get response code: " + response_code);
  if (response_code.equals(200)){
    def json = connection.getInputStream().getText()
    println("JSON: " + json)
    return json
  }
}

def parse_time_from_json(json){
  def result = new JsonSlurper().parseText(json)
  return result.time // get the time string
}

// Get the last digit of the minutes
def get_last_digit(){
  json = rest_api_get()
  time = parse_time_from_json(json)
  Integer last_digit = time[15] as Integer // get the last element
  println("The last digit is: " + last_digit)
  return last_digit
}

// Produce odd or even label based on the last digit
def produce_label(){
  last_digit = get_last_digit()
  if(last_digit % 2 == 0)
    return "even"
  else
    return "odd"
}

process get_label {
  output: 
    val label, emit: out

  exec:
    label = produce_label()
}

process branch_accordingly {
  echo true

  input:
    val label

  output:
    env OCRD_RESULT, emit: out

  script:
    if (label == "even") 
      """
      echo "The label is even."
      OCRD_RESULT="The label is 'even'."
      """
    else if (label == "odd")
      """
      echo "The label is odd."
      OCRD_RESULT="The label is 'odd'."
      """
    else
      """
      echo "The label is error."
      OCRD_RESULT="The label is 'error'."
      """
}

process print_branch_result {
  input:
    val message

  exec:
    println("The branching message is: " + message)
}

workflow {
  main:
    get_label()
    branch_accordingly(get_label.out)
    print_branch_result(branch_accordingly.out)
}
