from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
import re
from users.models import User
import json
from meiduo_mall.utils.info import InfoMixin
from django.shortcuts import redirect


class RegisterUserView(View):
    def post(self, request):
        # 接收请求
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        msg_code_sro = dict.get('sms_code')

        # 验证参数完整性
        if not all([username, password, password2, mobile, allow, msg_code_sro]):
            return JsonResponse({'code': 400, 'errmsg': '参数不完整'})

        # 用户名验证
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400, 'errmsg': 'username格式有误'})

        # 密码验证
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': 'password格式有误'})

        # 确认密码不一致性
        if password != password2:
            return JsonResponse({'code': 400, 'errmsg': '密码不一致性'})
        # 手机号验证
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400, 'errmsg': '手机格式有误'})
        # allow验证
        if allow != True:
            return JsonResponse({'code': 400, 'errmsg': 'allow格式有误'})

        # 短信验证 (链接redis)
        msg_redis_cli = get_redis_connection('msg_code')

        # 从redis中取值
        msg_code = msg_redis_cli.get(mobile)

        # 判断该值是否存在
        if not msg_code:
            return JsonResponse({'code': 400, 'errmsg': '短信验证码已过期'})
        # 短信验证码对比
        if msg_code_sro != msg_code.decode():
            return JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 保存到数据库 (username password mobile)
        try:
            # 使用create_user方法可以给密码加密处理
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '保存到数据库出错'})
        # 保持会话状态
        login(request, user)

        # 响应
        response = JsonResponse({'code': 0, 'errmsg': 'OK'})

        response.set_cookie('username', username, max_age=60 * 60 * 24 * 14)

        return response


class UserNameView(View):
    # 验证用户名是否重复
    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '数据库错误'})
        return JsonResponse({'code': 400, 'errmsg': '数据库错误', 'count': count})


class MobileView(View):
    # 验证手机号是否重复
    def get(self, request, mobile):
        try:
            count = User.objects.filter(moblie=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '数据库错误'})
        return JsonResponse({'code': 400, 'errmsg': '数据库错误', 'count': count})


class LoginView(View):
    def post(self, request):
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')
        if not all([username, password, remembered]):
            return JsonResponse({'code': 400, 'errmsg': '参数不完整'})
        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({'code': '400', 'errmsg': '用户名或者密码不正确'})
        # 状态保持
        login(request, user)

        if remembered != True:

            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        response = JsonResponse({'code': 0, 'errmsg': 'OK'})


        response.set_cookie('username', username, max_age=60 * 60 * 24 * 14)

        return response


class LogoutView(View):

    def delete(self, requset):
        # 断开会话状态
        logout(requset)
        response = JsonResponse({'code': 0, 'errmsg': 'OK'})
        # 删除保存在cookie里的用户信息
        response.delete_cookie('username')
        return response


class UserCenterInfoView(InfoMixin, View):
    def get(self, request):
        # pass
        # pass
        # this.username = response.data.info_data.username;
        # this.mobile = response.data.info_data.mobile;
        # this.email = response.data.info_data.email;
        # this.email_active = response.data.info_data.email_active;

        info_data = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            # 'email': request.user.email,
            # 'email_active': request.user.email_active,
        }
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'info_data': info_data})
