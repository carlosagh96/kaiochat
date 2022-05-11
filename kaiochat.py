#!/usr/bin/python3.9

################################################################################
# KAIOChat: Karurosagu's Asynchronous I/O Chat
################################################################################

import asyncio
import os
import sys
import yarl
import time
from aiohttp import web

try:
	the_port_raw=sys.argv[1]
	the_port=int(the_port_raw)
	assert the_port>0 and the_port<63999
except:
	_the_port="8080"
else:
	_the_port=str(the_port)

_html_page_main="""
<title>
KAIOChat
</title>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
div.msg_container{background-color:#DFDFDF;margin-left:4px;margin-right:4px;margin-top:4px;margin-bottom:4px;padding:8px}
</style>
</head>
"""

_html_page_script="""
<script>
var updating=false;
var send_message_isbusy=false;
var change_nickname_isbusy=false;

async function load_messages()
{
	if (!updating)
	{
		console.log("Updating messages...");

		updating=true;

		//let data = new FormData();
		//data.append("job","get_messages");

		let response=await fetch("/",
		{
			method:"post",
			headers:{"Accept":"text/html","Content-Type":"application/x-www-form-urlencoded"},
			body:"job=get_messages"
		});
		if (response.ok)
		{
			console.log("OK!");

			let html_dump=await response.text();
			if (html_dump.length>0)
			{
				console.log("Updated!");
				console.log(html_dump);
				document.getElementById("msg_container").innerHTML=html_dump;
			}
		}
		updating=false;
	}
}

async function change_nickname()
{
	console.log("Sending message...");
	payload=document.getElementById("change_nickname").name.value;
	payload=payload.trim()
	if (payload.length==0)
	{
		alert("This cannot be empty");
	}
	if (payload.length>64)
	{
		alert("The name is too long");
	}
	if ((!change_nickname_isbusy) && (payload.length>0) && (payload.length<65))
	{
		change_nickname_isbusy=true;
		let response=await fetch("/",
		{
			method:"post",
			headers:{"Accept":"text/plain","Content-Type":"application/x-www-form-urlencoded"},
			body:"job=change_nickname&payload="+payload
		});
		if (response.ok)
		{
			let log=await response.text();
			if (log.length>0)
			{
				alert(log);
			}
			else
			{
				document.getElementById("nickname").innerHTML=payload;
				document.getElementById("change_nickname").name.value="";
			}
		}
	}
	change_nickname_isbusy=false;
}

async function send_message()
{
	console.log("Sending message...");
	payload=document.getElementById("send_message").name.value;
	payload=payload.trim()
	if (payload.length==0)
	{
		alert("This cannot be empty");
	}
	if (payload.length>256)
	{
		alert("Message is too long")
	}
	if ((!send_message_isbusy) && (payload.length>0) && (payload.length<257))
	{
		send_message_isbusy=true;
		let response=await fetch("/",
		{
			method:"post",
			headers:{"Accept":"text/html","Content-Type":"application/x-www-form-urlencoded"},
			body:"job=send_message&payload="+payload
		});
		if (response.ok)
		{
			document.getElementById("send_message").name.value="";
			load_messages();
		}
	}
	send_message_isbusy=false;
}

window.setInterval(load_messages,1000);
</script>
"""

_html_page_forms_default="""
<div>
<p>Change nickname</p>
<form id="change_nickname" action="javascript:change_nickname()">
<input name="name" type="text" value="" autofocus>
<input type="submit" value="Change">
</form>
<p>Send a message</p>
<form id="send_message" action="javascript:send_message()">
<input name="name" type="text" value="" autofocus>
<input type="submit" value="Send">
</form>
</div>
<div>
</div>
"""

_html_page_messages="""
<div id="msg_container">

</div>
"""


_admin_address="::1"

_users={}
_messages=[]

class User:
	def __init__(self,uagent):
		self.uagent=uagent
		self.nickname=str(time.strftime("%Y-%m-%d-%H-%M-%S"))+"-"+str(len(_users))

	def debug_print(self,tabs=0):
		space="\t"*tabs
		print(space+"→ User-Agent:",self.uagent)
		print(space+"→ Nickname:",self.nickname)

	def html_nickname(self):
		return "<div><h3>Hello, <customtag id=\"nickname\">"+self.nickname+"</customtag></h3></div>\n"


class Message:
	def __init__(self,owner,content):
		self.owner=owner
		self.content=content

	def display_html(self):
		user=_users.get(self.owner)
		nick=user.nickname
		return "<div class=\"msg_container\"><span><h3>"+nick+"</h3></span><span>"+self.content+"</span></div>"

#################################################################################
# Handlers and app construction
#################################################################################

# GET requests
async def handler_get(request):
	print("GET Request by",request.remote)
	print("\t→ Browser/Client =",request.headers.get("User-Agent"))
	print("\t→ request.host =",request.host)
	print("\t→ request.url =",request.url)
	print("\t→ asks for request.rel_url =",request.rel_url)
	#yurl=yarl.URL(request.url)
	#print(yurl.query.keys)

	#response_text=_default_response
	response_mime="text/html"
	response_status=200

	detected_client=request.remote
	detected_uagent=request.headers.get("User-Agent")
	the_user=_users.get(detected_client)

	if the_user:
		print("\t\t→",detected_client,"is back again")
		if not the_user.uagent==detected_uagent:
			the_user.uagent=detected_uagent
			print("\t\t",detected_client,"changed the browser/client to",detected_uagent)

	if not the_user:
		the_user=User(detected_uagent)
		_users.update({detected_client:the_user})
		print("\t\t→ Added new user:",detected_client,"using",detected_uagent)

	the_user.debug_print(2)

	response_text=_html_page_main+_html_page_script+the_user.html_nickname()+_html_page_forms_default+_html_page_messages

	print("End of GET request by",request.remote)
	return web.Response(body=response_text,content_type=response_mime,charset="utf-8",status=response_status)

# POST requests
async def handler_post(request):
	print("POST Request by",request.remote)
	print("\t→ Browser/Client =",request.headers.get("User-Agent"))
	print("\t→ request.host =",request.host)
	print("\t→ request.url =",request.url)
	print("\t→ asks for request.rel_url =",request.rel_url)

	#yurl=yarl.URL(request.url)
	#print(yurl.query.keys)

	response_text=""
	response_mime="text/html"
	response_status=200

	detected_client=request.remote

	wutt=False
	the_user=_users.get(detected_client)
	if not the_user:
		wutt=True
		response_text="USER MISMATCH"
		response_mime="text/plain"
		response_status=400

	if not wutt:
		the_user.debug_print(2)
		post_data=await request.post()
		print("post_data =",post_data)
		job=post_data.get("job")
		if not job:
			wutt=True

	if not wutt:
		if job=="send_message" and post_data.get("payload"):
			message_text=post_data.get("payload")
			message_unit=Message(detected_client,message_text)
			_messages.append(message_unit)

		elif job=="change_nickname" and post_data.get("payload"):
			nickname_new=post_data.get("payload")
			exists=False
			for uid in _users:
				u=_users.get(uid)
				if nickname_new.upper()==u.nickname.upper():
					exists=True

				if exists:
					break

			if exists:
				response_text="Nickname already exists"
				response_mime="text/plain"

			else:
				the_user.nickname=nickname_new

		elif job=="get_messages":
			for message in _messages:
				response_text=message.display_html()+response_text

		else:
			wutt=True

	if wutt:
		print("SOMETHING FAILED IN HERE (._.)")
		response_status=400

	print("End of POST request by",request.remote)
	return web.Response(body=response_text,content_type=response_mime,charset="utf-8",status=response_status)

# Build the app
async def build_app():
	app=web.Application()
	app.add_routes([web.get("/",handler_get),web.post("/",handler_post)])
	return app

# Run the app
this_loop=asyncio.get_event_loop()
web.run_app(build_app(),port=_the_port)
