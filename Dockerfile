# Dockerfile for a Windows-based Python application
# using Python 3.11.8 on Windows Server Core LTSC 2022
FROM mcr.microsoft.com/windows/servercore:ltsc2022

ADD https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe python-installer.exe
RUN python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 && del python-installer.exe

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "Liberate\\app_princ.py"]