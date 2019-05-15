# -*- coding: utf-8 -*-
# @Author: Doctor Mu
# @Date:   2019-05-13 11:34:40
# @Last Modified by:   Doctor Mu
# @Last Modified time: 2019-05-13 20:47:23
import hashlib
import json
import redis
from django.http import HttpResponse
from datetime import datetime
from search.models import LcvUser


salt = "@doncgewei#$S.djkfhedasd~~~~!"


def user_list(req):
	if req.method == "POST":
		pageNum = req.POST.get("pageNum","1")
		pageNum = int(pageNum)
		users = LcvUser.objects.all().values("username","email","role","id","create_time").order_by("id")[pageNum-1:pageNum+9]
		userList = []
		for i in users:
			i['create_time'] = i['create_time'].strftime("%Y-%m-%d")
			userList.append(i)
		return HttpResponse(json.dumps({"status":0,"data":{"list":userList}}),content_type="application/json")



def md5_password(password):
	m1 = hashlib.md5()
	m1.update((salt+password).encode("utf-8"))
	return m1.hexdigest()

def login(req):
	# 检查用户名 -> 检查密码 -> 响应前端
	if req.method == "POST":
		username = req.POST.get('username','')
		response = LcvUser.objects.filter(username=username).count()
		if response == 0:
			return HttpResponse(json.dumps({"status":1,"msg":"用户名不存在"}),content_type="application/json")

		password = req.POST.get('password','')
		new_pass = md5_password(password)

		response = LcvUser.objects.filter(username=username,password=new_pass).count()
		if response == 0:
			return HttpResponse(json.dumps({"status":1,"msg":"密码错误"}),content_type="application/json")

		req.session['CURRENT_USER'] = username
		return HttpResponse(json.dumps({"status":0,"msg":"登录成功"}),content_type="application/json")

def logout(req):
	if req.method == "POST":
		req.session.flush()
		return HttpResponse(json.dumps({"status":0,"msg":"注销成功"}),content_type="application/json")


def register(req):
	# 检查用户名 -> 检查email -> 设置管理员 -> 密码md5加密 -> 写入数据 -> 响应前端
	if req.method == "POST":
		username = req.POST.get('username','')
		response = LcvUser.objects.filter(username=username).count()

		if response > 0:
			return HttpResponse(json.dumps({"status":1,"msg":"用户名已存在"}),content_type="application/json")


		email = req.POST.get('email','')
		response = LcvUser.objects.filter(email=email).count()
		if response > 0:
			return HttpResponse(json.dumps({"status":1,"msg":"email已存在"}),content_type="application/json")

		role = i

		password = req.POST.get('password','')
		new_pass = md5_password(password)

		user = LcvUser(username=username,password=new_pass,role=role,email=email,update_time=datetime.now(),create_time=datetime.now())
		user.save()
		return HttpResponse(json.dumps({"status":0,"msg":"注册成功"}),content_type="application/json")