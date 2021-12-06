      FROM python:latest
	  RUN python -m pip install --upgrade pip
	  WORKDIR /home/runner/work/OPERANDI_TestRepo/OPERANDI_TestRepo
      COPY . .
      CMD ["python", "./src/SimpleCode"]