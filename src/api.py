"""Small authenticated HTTP API for MY AI COMPANY. Run: python -m src.api"""
from __future__ import annotations
import hmac
import json
import os
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs
from src.orchestrator import create_task
from src.storage import BUSINESSES, decide_approval, list_approvals, list_tasks, save_task, initialize

TOKEN = os.environ.get("MYAI_API_TOKEN", "")
MAX_BODY = 32_768

def response(start_response, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode()
    start_response(status, [("Content-Type","application/json; charset=utf-8"),
                            ("Content-Length",str(len(body))),
                            ("Cache-Control","no-store")])
    return [body]

def app(environ, start_response):
    method, path = environ.get("REQUEST_METHOD","GET"), environ.get("PATH_INFO","/")
    if path == "/health" and method == "GET":
        return response(start_response,"200 OK",{"status":"ok","service":"my-ai-company-api","mode":"mvp"})
    if not TOKEN:
        return response(start_response,"503 Service Unavailable",{"error":"API is not configured. Set MYAI_API_TOKEN."})
    supplied = environ.get("HTTP_AUTHORIZATION","")
    if not supplied.startswith("Bearer ") or not hmac.compare_digest(supplied[7:],TOKEN):
        return response(start_response,"401 Unauthorized",{"error":"Authentication required"})
    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) < 2 or parts[0] != "api" or parts[1] not in BUSINESSES:
        return response(start_response,"404 Not Found",{"error":"Route or business workspace not found"})
    business = parts[1]
    try:
        initialize(business)
        if len(parts)==3 and parts[2]=="tasks" and method=="GET":
            query=parse_qs(environ.get("QUERY_STRING",""))
            status=query.get("status",[None])[0]
            return response(start_response,"200 OK",{"business":business,"tasks":list_tasks(business,status)})
        if len(parts)==3 and parts[2]=="tasks" and method=="POST":
            length=int(environ.get("CONTENT_LENGTH") or 0)
            if length<=0 or length>MAX_BODY:
                return response(start_response,"413 Content Too Large",{"error":"Request body missing or too large"})
            data=json.loads(environ["wsgi.input"].read(length))
            if not isinstance(data, dict):
                raise ValueError("Request body must be a JSON object")
            task_type, description = data.get("task_type"), data.get("description")
            action = data.get("action")
            if not isinstance(task_type, str) or not isinstance(description, str) or not description.strip():
                raise ValueError("task_type and a non-empty description are required")
            if action is not None and not isinstance(action, str):
                raise ValueError("action must be a string")
            task=create_task(business,task_type,description.strip(),action,persist_file=False)
            save_task(task)
            return response(start_response,"201 Created",task)
        if len(parts)==3 and parts[2]=="approvals" and method=="GET":
            return response(start_response,"200 OK",{"business":business,"approvals":list_approvals(business)})
        if len(parts)==5 and parts[2]=="approvals" and parts[4]=="decision" and method=="POST":
            length=int(environ.get("CONTENT_LENGTH") or 0)
            if length<=0 or length>MAX_BODY:
                return response(start_response,"413 Content Too Large",{"error":"Request body missing or too large"})
            data=json.loads(environ["wsgi.input"].read(length))
            ok=decide_approval(business,parts[3],data.get("decision",""),data.get("note",""))
            return response(start_response,"200 OK" if ok else "409 Conflict",{"updated":ok})
        return response(start_response,"404 Not Found",{"error":"Endpoint not found"})
    except (ValueError,KeyError,json.JSONDecodeError) as exc:
        return response(start_response,"400 Bad Request",{"error":str(exc)})
    except Exception:
        return response(start_response,"500 Internal Server Error",{"error":"Internal server error"})

def main():
    host=os.environ.get("MYAI_HOST","127.0.0.1")
    port=int(os.environ.get("MYAI_PORT","8080"))
    if not TOKEN:
        raise SystemExit("Set MYAI_API_TOKEN before starting the API.")
    for business in BUSINESSES: initialize(business)
    print(f"MY AI COMPANY API listening on http://{host}:{port}")
    with make_server(host,port,app) as server: server.serve_forever()

if __name__=="__main__": main()
