# -*- coding: utf-8 -*-

import sys, os
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if p not in sys.path:
    sys.path.insert(0, p)

from qqbot.utf8logger import ERROR, DEBUG
from qqbot.qqbotcls import QQBot, QQBotSlot as qqbotslot
from qqbot.mainloop import Put
from qqbot.common import Unquote, STR2BYTES, JsonDumps

@qqbotslot
def onQQMessage(bot, contact, member, content):
    # 当收到 QQ 消息时被调用
    # bot     : QQBot 对象，提供 List/SendTo/Stop/Restart 四个接口，详见文档第五节
    # contact : QContact 对象，消息的发送者，具有 ctype/qq/uin/name/nick/mark/card 属性，这些属性都是 str 对象
    # member  : QContact 对象，仅当本消息为 群或讨论组 消息时有效，代表实际发消息的成员
    # content : str 对象，消息内容
    if content == '--version':
        bot.SendTo(contact, 'QQbot-' + bot.conf.version)

@qqbotslot
def onNewContact(bot, contact, owner):
    # 当新增 好友/群/讨论组/群成员/讨论组成员 时被调用
    # 一般情况下联系人变动事件延后 5 ~ 10 分钟，可以将关心的联系人列表加入到配置文件的 monitorTables 中去
    # 若 monitorTables 中的列表数量较少，则被监视的列表中的联系人变动事件延后时间将大幅缩短
    # bot     : QQBot 对象
    # contact : QContact 对象，代表新增的联系人
    # owner   : QContact 对象，仅在新增 群成员/讨论组成员 时有效，代表新增成员所在的 群/讨论组
    pass

@qqbotslot
def onLostContact(bot, contact, owner):
    # 当失去 好友/群/讨论组/群成员/讨论组成员 时被调用
    # 一般情况下联系人变动事件延后 5 ~ 10 分钟，可以将关心的联系人列表加入到配置文件的 monitorTables 中去
    # 若 monitorTables 中的列表数量较少，则被监视的列表中的联系人变动事件延后时间将大幅缩短
    # bot     : QQBot 对象
    # contact : QContact 对象，代表失去的联系人
    # owner   : QContact 对象，仅在失去 群成员/讨论组成员 时有效，代表失去成员所在的 群/讨论组
    pass

@qqbotslot
def onInterval(bot):
    # 每隔 5 分钟被调用
    # bot : QQBot 对象
    DEBUG('INTERVAL')

@qqbotslot
def onStartupComplete(bot):
    # 完成启动是被调用（此时已登录成功，且开始监听消息和 qterm 客户端命令）
    # bot : QQBot 对象
    DEBUG('START-UP-COMPLETE')
    pass

@qqbotslot
def onFetchComplete(bot):
    # 完成一轮联系人列表刷新时被调用
    # bot : QQBot 对象
    DEBUG('FETCH-COMPLETE')
    pass

def onTermCommand(bot, client, command):
    # DEBUG(command)

    if command.startswith('GET /'):
        http = True
        end = command.find('\r\n')
        if end == -1 or not command[:end-3].endswith(' HTTP/'):
            argv = []
        else:
            url = command[5:end-9].rstrip('/')
            if url == 'favicon.ico':
                # DEBUG('close')
                client.Reply('')
                return
            argv = [Unquote(x) for x in url.split('/')]
    else:
        http = False
        argv = command.strip().split(None, 3)

    if argv and argv[0] in cmdFuncs:
        try:
            result, err = cmdFuncs[argv[0]](bot, argv[1:], http)
        except (Exception, SystemExit) as e:
            result, err = None, '运行命令过程中出错：' + str(type(e)) + str(e)
            ERROR(err, exc_info=True)
    else:
        result, err = None, 'QQBot 命令格式错误'
    
    if http:
        rep = {'result':result, 'err': err}
        rep = STR2BYTES(JsonDumps(rep, ensure_ascii=False, indent=4))
        rep = (b'HTTP/1.1 200 OK\r\n' +
               b'Connection: close\r\n' + 
               b'Content-Length: ' + STR2BYTES(str(len(rep))) + b'\r\n' +
               b'Content-Type: text/plain;charset=utf-8\r\n\r\n' +
               rep)
    else:
        rep = STR2BYTES(str(err or result)) + b'\r\n'

    client.Reply(rep)

QQBot.onTermCommand = onTermCommand

cmdFuncs, usage = {}, {}

def cmd_help(bot, args, http=False):
    '''1 help'''
    if len(args) == 0:
        return usage['term'], None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_stop(bot, args, http=False):
    '''1 stop'''
    if len(args) == 0:
        Put(bot.Stop)
        return 'QQBot已停止', None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_restart(bot, args, http=False):
    '''1 restart'''
    if len(args) == 0:
        Put(bot.Restart)
        return 'QQBot已重启', None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_list(bot, args, http=False):
    '''2 list buddy|group|discuss [qq|name|key=val]
       2 list group-member|discuss-member oqq|oname|okey=oval [qq|name|key=val]'''
    
    if (len(args) in (1, 2)) and args[0] in ('buddy', 'group', 'discuss'):
        # list buddy
        # list buddy jack
        if not http:
            return bot.StrOfList(*args), None
        else:
            return bot.ObjOfList(*args)            
        
    elif (len(args) in (2, 3)) and args[1] and (args[0] in ('group-member', 'discuss-member')):
        # list group-member xxx班
        # list group-member xxx班 yyy
        if not http:
            return bot.StrOfList(*args), None
        else:
            return bot.ObjOfList(*args)
        
    else:
        return None, 'QQBot 命令格式错误'

def cmd_update(bot, args, http=False):
    '''2 update buddy|group|discuss
       2 update group-member|discuss-member oqq|oname|okey=oval'''
    
    if len(args) == 1 and args[0] in ('buddy', 'group', 'discuss'):
        # update buddy
        return bot.Update(args[0]), None    
    elif len(args) == 2 and args[1] and (args[0] in ('group-member', 'discuss-member')):
        # update group-member xxx班
        cl = bot.List(args[0][:-7], args[1])
        if cl is None:
            return None, 'QQBot 在向 QQ 服务器请求数据获取联系人资料的过程中发生错误'
        elif not cl:
            return None, '%s-%s 不存在' % (args[0], args[1])
        else:
            return [bot.Update(c) for c in cl], None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_send(bot, args, http=False):
    '''3 send buddy|group|discuss qq|name|key=val message'''
    
    if len(args) == 3 and args[0] in ('buddy', 'group', 'discuss'):
        # send buddy jack hello
        cl = bot.List(args[0], args[1])
        if cl is None:
            return None, 'QQBot 在向 QQ 服务器请求数据获取联系人资料的过程中发生错误'
        elif not cl:
            return None, '%s-%s 不存在' % (args[0], args[1])
        else:
            msg = args[2].replace('\\n','\n').replace('\\t','\t')
            result = [bot.SendTo(c, msg) for c in cl]
            if not http:
                result = '\n'.join(result)
            return result, None
    else:
        return None, 'QQBot 命令格式错误'

def group_operation(bot, ginfo, minfos, func, exArgs, http):
    gl = bot.List('group', ginfo)
    if gl is None:
        return None, '错误：向 QQ 服务器请求群列表失败'
    elif not gl:
        return None, '错误：群%s 不存在' % ginfo

    result = []
    for g in gl:
        membsResult, membs = [], []

        for minfo in minfos:
            ml = bot.List(g, minfo)
            if ml is None:
                membsResult.append('错误：向 QQ 服务器请求%s的成员列表失败' % g)
            elif not ml:
                membsResult.append('错误：%s[成员“%s”]不存在' % (g, minfo))
            else:
                membs.extend(ml)

        if membs:
            membsResult.extend(func(g, membs, *exArgs))

        if not http:
            result.append('\n'.join(membsResult))
        else:
            result.append({'group': g.__dict__, 'membs_result': membsResult})
    
    if not http:
        result = '\n\n'.join(result)
    
    return result, None

def cmd_group_kick(bot, args, http=False):
    '''4 group-kick ginfo minfo1,minfo2,minfo3'''
    if len(args) == 2:
        ginfo = args[0]
        minfos = args[1].split(',')
        return group_operation(bot, ginfo, minfos, bot.GroupKick, [], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_group_set_admin(bot, args, http=False):
    '''4 group-set-admin ginfo minfo1,minfo2,minfo3'''
    if len(args) == 2:
        ginfo = args[0]
        minfos = args[1].split(',')
        return group_operation(bot, ginfo, minfos, bot.GroupSetAdmin, [True], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_group_unset_admin(bot, args, http=False):
    '''4 group-unset-admin ginfo minfo1,minfo2,minfo3'''
    if len(args) == 2:
        ginfo = args[0]
        minfos = args[1].split(',')
        return group_operation(bot, ginfo, minfos, bot.GroupSetAdmin, [False], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_group_shut(bot, args, http=False):
    '''4 group-shut ginfo minfo1,minfo2,minfo3 t'''
    if len(args) in (2, 3):
        ginfo = args[0]
        minfos = args[1].split(',')
        if len(args) == 3 and args[2].isdigit() and int(args[2]) > 60:
            t = int(args[2])
        else:
            t = 60
        return group_operation(bot, ginfo, minfos, bot.GroupShut, [t], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_group_set_card(bot, args, http=False):
    '''4 group-set-card ginfo minfo1,minfo2,minfo3 card'''
    if len(args) == 3:
        ginfo = args[0]
        minfos = args[1].split(',')
        card = args[2]
        return group_operation(bot, ginfo, minfos, bot.GroupSetCard, [card], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_group_unset_card(bot, args, http=False):
    '''4 group-unset-card ginfo minfo1,minfo2,minfo3'''
    if len(args) == 2:
        ginfo = args[0]
        minfos = args[1].split(',')
        card = ''
        return group_operation(bot, ginfo, minfos, bot.GroupSetCard, [card], http)
    else:
        return None, 'QQBot 命令格式错误'

def cmd_plug(bot, args, http=False):
    '''5 plug myplugin'''
    if len(args) == 1:
        return bot.Plug(args[0]), None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_unplug(bot, args, http=False):
    '''5 unplug myplugin'''
    if len(args) == 1:
        return bot.Unplug(args[0]), None
    else:
        return None, 'QQBot 命令格式错误'

def cmd_plugins(bot, args, http=False):
    '''5 plugins'''
    if len(args) == 0:
        if not http:
            return '已加载插件：%s' % bot.Plugins(), None
        else:
            return bot.Plugins(), None
    else:
        return None, 'QQBot 命令格式错误'
                    
for name, attr in dict(globals().items()).items():
    if name.startswith('cmd_'):
        cmdFuncs[name[4:].replace('_', '-')] = attr

usage['term'] = '''\
QQBot 命令：
1） 帮助、停机和重启命令
    qq help|stop|restart

2） 联系人查询命令
    qq list buddy|group|discuss [qq|name|key=val]
    qq list group-member|discuss-member oqq|oname|okey=oval [qq|name|key=val]

3） 联系人更新命令
    qq update buddy|group|discuss
    qq update group-member|discuss-member oqq|oname|okey=oval

4） 消息发送命令
    qq send buddy|group|discuss qq|name|key=val message

5） 群管理命令： 设置/取消管理员 、 设置/删除群名片 、 群成员禁言 以及 踢除群成员
    qq group-set-admin ginfo minfo1,minfo2,...
    qq group-unset-admin ginfo minfo1,minfo2,...
    qq group-set-card ginfo minfo1,minfo2,... card
    qq group-unset-card ginfo minfo1,minfo2,...
    qq group-shut ginfo minfo1,minfo2,... [t]
    qq group-kick ginfo minfo1,minfo2,...

6） 加载/卸载/显示插件
    qq plug/unplug myplugin
    qq plugins\
'''