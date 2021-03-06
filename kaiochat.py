#!/usr/bin/python3.9

################################################################################
# KAIOChat: Karurosagu's Asynchronous I/O Chat
################################################################################

import aiohttp
import asyncio
import os
import sys
import yarl
import time

from aiohttp import web
from hashlib import md5
from pprint import pformat

try:
	the_port_raw=sys.argv[1]
	the_port=int(the_port_raw)
	assert the_port>0 and the_port<63999
except:
	_the_port="8080"
else:
	_the_port=str(the_port)

################################################################################
# Frontend stuff
################################################################################

_html_page_main="""
<title>
KAIOChat
</title>
<head>
<meta content="text/html;charset=utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
#msg_container,#reply_to {padding-top:8px}

div.message {background-color:#DFDFDF;margin-top:8px;margin-bottom:8px;padding-left:16px;padding-right:16px;padding-bottom:2px;padding-top:2px}
div.tools {padding-bottom:8px;padding-top:8px;}
div.hidden {display:none!important}
div.show {display:block!important}

p.om {background-color: #CACACC;padding:8px}
body {margin-left:16px;margin-right:16px}

input {border:2px solid;padding:8px 16px;width:300px}
textarea {min-width:320px;width:100%;max-width:100%;min-height:96px;max-height:96px;font-size:16px;border: 2px solid;padding:8px 16px}

button {border:2px solid black;padding:8px 16px;text-align:center;text-decoration:none;display:inline-block;cursor:pointer}
button {background-color:black;color:white}
button:hover {background-color:grey;border:2px solid grey}
button:active {background-color:white;color:black;border:2px solid black}
button.tab {float:left}
button.tab_now {background-color:white;color:black}
button.tab_now:hover {background-color:white;border:2px solid black}

</style>
</head>
"""

_html_page_script="""
<script>

var sock=new WebSocket("WEBSOCKETS_URL");

var updating=false;
var msg_latest="";
var msg_target="";
var room="LAST_ROOM_VISITED";

const tabs=["send_message","room_config","profile_settings"];
const tabs_len=tabs.length;

//function room_set(name)
//{
//	if (document.getElementById("room_name").innerHTML==name)
//	{
//		console.log("No need to change the room")
//	}
//	{
//		room=name;
//		document.getElementById("room_name").innerHTML=name;
//	}
//}

function chat_update(full)
{
	if (!updating && room.length>0)
	{
		updating=true;
		let the_data="update"+"&room="+room;
		if (msg_latest.length>0)
		{
			the_data=the_data+"&msg_latest="+msg_latest;
		}
		sock.send(the_data);
		updating=false;
	}
}

function from_socket(event)
{

	let empty=true;
	if (msg_latest.length>0)
	{
		empty=false;
	}
	let html_dump=event.data.slice(33);
	msg_latest=event.data.slice(0,32);
	if (html_dump.length>0)
	{
		msg_container=document.getElementById("msg_container");
		if (msg_container.innerHTML==html_dump)
		{
			console.log("\tMessages have not changed");
		}
		else
		{
			if (empty)
			{
				msg_container.innerHTML=html_dump;
			}
			else
			{
				msg_container.innerHTML=html_dump+msg_container.innerHTML;
			}
		}
	}
}

async function post_data(data_job)
{
	data_payload=document.getElementById(data_job+"_1").value;
	data_payload=data_payload.trim()
	let the_body="";
	if (data_job=="send_message")
	{
		the_body="job="+data_job+"&room="+room;
		if (msg_target.length>0)
		{
			the_body=the_body+"&msg_target="+msg_target;
		}
		the_body=the_body+"&payload="+data_payload;
		select_message_null();
	}
	if (data_job=="profile_settings")
	{
		the_body="job="+data_job+"&payload="+data_payload;
	}
	let response=await fetch("/",
	{
		method:"post",
		headers:{"Accept":"text/plain","Content-Type":"application/x-www-form-urlencoded"},
		body:the_body
	});
	if (response.ok)
	{
		if (data_job=="send_message")
		{
			document.getElementById("send_message_1").value="";
			chat_update();
		}
		if (data_job=="profile_settings")
		{
			let log=await response.text();
			if (log.length>0)
			{
				alert(log);
			}
			else
			{
				let oldname=document.getElementById("nickname").innerHTML;
				document.getElementById("nickname").innerHTML=data_payload;
				document.getElementById("profile_settings_1").value="";
				let messages_all=document.getElementsByClassName("message");
				let messages_num=messages_all.length;
				let idx=0;
				while (idx<messages_num)
				{
					curr_msg=messages_all[idx];
					tag_h3=curr_msg.getElementsByTagName("h3")[0];
					if (tag_h3.innerHTML==oldname)
					{
						tag_h3.innerHTML=data_payload;
					}
					idx=idx+1;
				}
			}
		}
	}
}

function select_message_null()
{
	if (msg_target.length>0)
	{
		msg_target="";
		document.getElementById("shipment").innerHTML="Send message";
	}
}

function select_message_reply(given_id)
{
	if (msg_target==given_id)
	{
		select_message_null();
	}
	else
	{
		msg_target=given_id;
		document.getElementById("shipment").innerHTML="Answer <a href='#"+given_id+"'>this message</a> <button onclick='javascript:select_message_null()'>Cancel</button>";
	}
}

function is_visible(id)
{
	let thing=document.getElementById(id);
	if ((thing.className.indexOf("hidden")>-1))
	{
		return false;
	}
	else
	{
		return true;
	}
}

function show_tab(selected)
{
	let vvv=is_visible(selected);
	if (!vvv)
	{
		let idx=0;
		let curr="";
		while (idx<tabs_len)
		{
			curr=tabs[idx];
			vvv=is_visible(curr);
			if (curr==selected)
			{
				if (!vvv)
				{
					let doc_elem1=document.getElementById(curr);
					let doc_elem2=document.getElementById("tab_"+curr);
					doc_elem1.className=doc_elem1.className.replace("hidden","show");
					doc_elem2.className=doc_elem2.className+" tab_now";
				}
				if (selected=="room_config")
				{
					let room_tag=document.getElementById("room_name");
					if (room_tag.innerHTML==room)
					{
						console.log("No need to change the room tag")
					}
					else
					{
						room_tag.innerHTML=room;
					}
				}
			}
			else
			{
				if (vvv)
				{
					let doc_elem1=document.getElementById(curr);
					let doc_elem2=document.getElementById("tab_"+curr);
					doc_elem1.className=doc_elem1.className.replace("show","hidden");
					doc_elem2.className=doc_elem2.className.replace(" tab_now","");
				}
			}
			idx=idx+1;
		}
	}
}

sock.addEventListener("message",from_socket);
window.setInterval(chat_update,1000);
</script>
"""

_html_page_default="""
<div class="tools">
<button id="tab_send_message" class="tab tab_now" onclick="javascript:show_tab('send_message')">Messaging</button>
<button id="tab_room_config" class="tab" onclick="javascript:show_tab('room_config')">Rooms</button>
<button id="tab_profile_settings" class="tab" onclick="javascript:show_tab('profile_settings')">Profile</button>
</div>

<!-- Messaging tab -->
<div id="send_message" class="show" style="clear:both;padding-top:8px">
<p id="shipment">Send text message</p>
<span>
<textarea id="send_message_1" placeholder="Write message here" minlength="1" maxlength="256"></textarea>

<p><button id="send_message_btn" onclick="javascript:post_data('send_message')">Send it</button></p>
</span>

<div id="msg_container">

</div>

</div>

<!-- Rooms tab -->
<div id="room_config" class="hidden" style="clear:both;padding-top:8px">
<p>Rooms</p>
<p>Current room: <custom id="room_name"></custom></p>
</div>

<!-- Profile settings tab -->
<div id="profile_settings" class="hidden" style="clear:both;padding-top:8px">
<p>Profile Settings</p>
<span>
<input id="profile_settings_1" minlength=1 maxlength=32 placeholder="New nickname" type="text" value="">
<button id="profile_settings_btn" onclick="javascript:post_data('profile_settings')">Change</button>
</span>
</div>
"""

################################################################################
# Backend stuff
################################################################################

def time_stamp():
	return str(time.strftime("%Y-%m-%d-%H-%M-%S"))

_admin_address="::1"

_users={}

class User:
	def __init__(self,uagent,ip):
		self.uagent=uagent
		self.nickname="User "+time_stamp()+"-"+str(len(_users))
		self.last_room="Master"

		if ip==_admin_address:
			self.is_admin=True
		else:
			self.is_admin=False


	def debug_print(self,tabs=0):
		space="\t"*tabs
		print(space+"??? User-Agent:",self.uagent)
		print(space+"??? Nickname:",self.nickname)

	def html_nickname(self):
		return "<div><h3>Hello, <customtag id=\"nickname\">"+self.nickname+"</customtag></h3></div>\n"

class Message:
	def __init__(self,room,owner,content,reply):
		shit=owner+" "+time_stamp()
		self.mid=md5(shit.encode()).hexdigest()
		self.room=room
		self.owner=owner
		self.content=content
		self.reply=reply

	def display_html(self):
		user=_users.get(self.owner)
		nick=user.nickname

		om=""
		the_buttons="<button onclick=\"javascript:select_message_reply('"+self.mid+"')\">Select</button> "
		if self.reply:
			the_room=_rooms.get(self.room)
			for msg in the_room.messages:
				if msg.mid==self.reply:
					us=_users.get(msg.owner)
					nm=us.nickname
					txt=msg.content
					if len(txt)>64:
						txt=txt[0:64]+"..."

					om="<p class=\"om\"><strong>"+nm+"</strong> <i>"+txt+"</i></p>"
					break

			the_buttons=the_buttons+"<a href=#"+self.reply+"><button float=right>Go to OM</button></a>"

		return "<div class=\"message\" id=\""+self.mid+"\" class=\"msg_container\"><h3>"+nick+"</h3>"+om+"<p>"+self.content.replace("\n","<br>")+"</p><div name=\"msg_actions\"><p>"+the_buttons+"</p></div></div>\n"

class Room:
	def __init__(self,owner):
		self.owner=owner
		self.messages=[]

	def msg_get(self,latest=None):
		htmldump=""
		if latest:
			add_next=False
			for msg in self.messages:
				if not add_next:
					if latest==msg.mid:
						add_next=True
				else:
					htmldump=msg.display_html()+htmldump

		if not latest:
			for msg in self.messages:
				htmldump=msg.display_html()+htmldump

		if len(htmldump)>0:
			htmldump=msg.mid+" "+htmldump

		return htmldump

	def msg_add(self,room,owner,content,reply):
		message_unit=Message(room,owner,content,reply)
		self.messages.append(message_unit)

_rooms={"Master":Room("")}

#################################################################################
# Handlers and app construction
#################################################################################

# WebSockets requests
async def handler_ws(request):
	print("WS Request by",request.remote)
	print("\t??? Browser/Client =",request.headers.get("User-Agent"))
	# print("\t??? Token =",request.headers.get("Authorization"))
	print("\t??? request.host =",request.host)
	print("\t??? request.url =",request.url)
	print("\t??? asks for request.rel_url =",request.rel_url)

	token=request.cookies.get("KAIOChat_Token")
	if not token:
		print("NO TOKEN?????")
		return None

	the_user=_users.get(token)

	if not the_user:
		print("NO USER?????")
		return None

	ws=web.WebSocketResponse()
	await ws.prepare(request)
	async for msg in ws:
		if msg.type == aiohttp.WSMsgType.TEXT:
			if msg.data=="close":
				print("\t\tWS Connection closed")
				await ws.close()

			else:
				y=yarl.URL("/?"+msg.data)

				response=""
				message=None

				post_data=y.query
				# data_room=post_data.get("room")
				# print("post_data =",post_data)
				msg_latest=post_data.get("msg_latest")
				room=post_data.get("room")
				if room:
					the_room=_rooms.get(room)
					if the_room:
						response=the_room.msg_get(msg_latest)
						the_user.last_room=room

				if message and len(response)>0:
					response=message.mid+" "+response

				if len(response)>0:
					print("RESPONSE\n"+response)
					await ws.send_str(response)

		elif msg.type == aiohttp.WSMsgType.ERROR:
			print("\t\tWS Connection closed with exception",ws.exception())

	return ws

# GET requests
async def handler_get(request):
	print("GET Request by",request.remote)
	print("\t??? Browser/Client =",request.headers.get("User-Agent"))
	print("\t??? request.host =",request.host)
	print("\t??? request.url =",request.url)
	print("\t??? asks for request.rel_url =",request.rel_url)

	yurl=yarl.URL(request.url)
	response_mime="text/html"
	response_status=200

	token=request.cookies.get("KAIOChat_Token")
	print("\t??? Token =",token)

	if token:
		the_user=_users.get(token)
	else:
		the_user=None

	if not the_user:

		detected_uagent=request.headers.get("User-Agent")
		detected_client=request.remote

		data_involved=detected_uagent+" "+detected_client

		token=md5(data_involved.encode()).hexdigest()

		the_user=User(detected_uagent,detected_client)
		_users.update({token:the_user})
		print("\t\t??? Added new user:",detected_client,"using",detected_uagent)

	# WEBSOCKETS URL
	ws_url=str(yurl)
	if yurl.scheme=="http":
		ws_url=ws_url.replace("http://","ws://")
	else:
		ws_url=ws_url.replace("https://","wss://")

	if not ws_url.endswith("/"):
		ws_url=ws_url+"/"

	ws_url=ws_url+"ws"
	html_scr=_html_page_script.replace("WEBSOCKETS_URL",ws_url)

	# USER TOKEN
	html_scr=html_scr.replace("USER_TOKEN",token)

	# ROOM NAME
	html_scr=html_scr.replace("LAST_ROOM_VISITED",the_user.last_room)

	response_text=_html_page_main+html_scr+the_user.html_nickname()+_html_page_default

	print("End of GET request by",request.remote)
	response=web.Response(body=response_text,content_type=response_mime,charset="utf-8",status=response_status)
	response.set_cookie("KAIOChat_Token",token,samesite="Strict")
	return response

# POST requests
async def handler_post(request):
	print("POST Request by",request.remote)
	print("\t??? Browser/Client =",request.headers.get("User-Agent"))
	print("\t??? request.host =",request.host)
	print("\t??? request.url =",request.url)
	print("\t??? asks for request.rel_url =",request.rel_url)

	response_text=""
	response_mime="text/html"
	response_status=200

	wutt=False

	token=request.cookies.get("KAIOChat_Token")
	print("\t??? Token =",token)

	if token:
		the_user=_users.get(token)
	else:
		the_user=None

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
			msg_target=post_data.get("msg_target")
			room=post_data.get("room")
			if room:
				the_room=_rooms.get(room)
				if the_room:
					the_room.msg_add(room,token,message_text,msg_target)

		elif job=="profile_settings" and post_data.get("payload"):
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

		elif job=="create_thread" and post_data.get("thread"):
			new=post_data.get("thread")
			if not (new in _rooms):
				response_text="Thread already exists"

			

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
	app.add_routes([web.get("/",handler_get),web.post("/",handler_post),web.get("/ws",handler_ws)])
	return app

print("KAIOChat v2022-05-21\n\tWritten by ???????????????\n\tTelegram: https://t.me/CarlosAGH\n")

# Run the app
this_loop=asyncio.get_event_loop()
web.run_app(build_app(),port=_the_port)
