@echo off
title Mission Control — Audiper
echo Iniciando Mission Control em http://localhost:8080/mission-control.html
cd /d D:\Site\audiper
start "" "http://localhost:8080/mission-control.html"
npx http-server . -p 8080 --cors -c-1
