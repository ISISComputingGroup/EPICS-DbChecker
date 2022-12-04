@echo off
setlocal
%PYTHON3% %~dp0check_db_file.py -o %~dp0..\..\..\test-reports -d %~dp0..\..\.. -r
