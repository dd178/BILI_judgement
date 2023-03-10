#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2021-10-01 0:28
# @Author  : 178

import asyncio
import json
import os
import sys
import time
import random
import logging
import aiohttp
import traceback
# import platform
from collections import OrderedDict

_debug = False


class asyncBiliApi(object):
    '''B站异步接口类'''

    def __init__(self,
                 headers: dict
                 ):
        self._islogin = False
        self._show_name = None
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=50, force_close=True)
        self._session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        )

    async def login_by_cookie(self,
                              cookieData,
                              checkBanned=True,
                              strict=False
                              ):
        '''
        登录并获取账户信息
        cookieData dict 账户cookie
        checkBanned bool 检查是否被封禁
        strict bool 是否严格限制cookie在.bilibili.com域名之下
        '''
        if strict:
            from yarl import URL
            self._session.cookie_jar.update_cookies(
                cookieData, URL('https://.bilibili.com'))
        else:
            self._session.cookie_jar.update_cookies(cookieData)

        await self.refreshInfo()
        if not self._islogin:
            return False

        if 'bili_jct' in cookieData:
            self._bili_jct = cookieData["bili_jct"]
        else:
            self._bili_jct = ''

        self._isBanned = None
        if checkBanned:
            code = (await self.likeCv(7793107))["code"]
            if code != 0 and code != 65006 and code != -404:
                self._isBanned = True
                import warnings
                warnings.warn(f'{self._name}:账号异常，请检查bili_jct参数是否有效或本账号是否被封禁')
            else:
                self._isBanned = False

        return True

    async def refreshInfo(self):
        '''刷新账户信息(需要先登录)'''
        ret = await self.getWebNav()
        if ret["code"] != 0:
            self._islogin = False
            return

        self._islogin = True
        self._name = ret["data"]["uname"]
        if not self._show_name:
            self._show_name = self._name

    @property
    def name(self) -> str:
        '''获取用于显示的用户名'''
        return self._show_name

    async def getWebNav(self):
        '''获取导航信息'''
        url = "https://api.bilibili.com/x/web-interface/nav"
        async with self._session.get(url, verify_ssl=False) as r:
            ret = await r.json()
        return ret

    async def likeCv(self,
                     cvid: int,
                     type=1):
        '''
        点赞专栏
        cvid int 专栏id
        type int 类型
        '''
        url = 'https://api.bilibili.com/x/article/like'
        post_data = {
            "id": cvid,
            "type": type,
            "csrf": self._bili_jct
        }
        async with self._session.post(url, data=post_data, verify_ssl=False) as r:
            return await r.json()

    async def juryInfo(self):
        '''
        取当前账户风纪委员状态
        '''
        url = 'https://api.bilibili.com/x/credit/v2/jury/jury'
        async with self._session.get(url, verify_ssl=False) as r:
            return await r.json()

    async def juryapply(self):
        '''
        申请风纪委员资格
        '''
        url = 'https://api.bilibili.com/x/credit/v2/jury/apply'
        post_data = {
            "csrf": self._bili_jct
        }
        async with self._session.post(url, data=post_data, verify_ssl=False) as r:
            return await r.json()

    async def juryCaseInfo(self,
                           case_id: str
                           ):
        '''
        获取风纪委员案件信息
        '''
        url = f'https://api.bilibili.com/x/credit/v2/jury/case/info?case_id={case_id}'
        async with self._session.get(url, verify_ssl=False) as r:
            return await r.json()

    async def juryCaseObtain(self):
        '''
        拉取一个案件用于风纪委员投票
        '''
        url = 'https://api.bilibili.com/x/credit/v2/jury/case/next'
        post_data = {
            "csrf": self._bili_jct
        }
        async with self._session.get(url, data=post_data, verify_ssl=False) as r:
            return await r.json()

    async def juryopinion(self,
                          case_id: str
                          ):
        '''
        获取风纪委员案件众议观点
        '''
        url = f'https://api.bilibili.com/x/credit/v2/jury/case/opinion?case_id={case_id}&pn=1&ps=20'
        async with self._session.get(url, verify_ssl=False) as r:
            return await r.json()

    async def juryVote(self,
                       case_id: str,
                       vote: int,
                       anonymous: int = 0,
                       ):
        '''风纪委员案件投票'''
        url = 'https://api.bilibili.com/x/credit/v2/jury/vote'
        post_data = {
            "case_id": case_id,  # 案件id
            "vote": vote,  # 投票选项
            "csrf": self._bili_jct,  # 验证
            "insiders": random.choice([0, 1]),  # 是否观看
            "anonymous": anonymous  # 是否匿名
        }
        async with self._session.post(url, data=post_data, verify_ssl=False) as r:
            return await r.json()

    async def juryList(self):
        '''获取最近20条已投票案件'''
        url = 'https://api.bilibili.com/x/credit/v2/jury/case/list?pn=1&ps=20'
        async with self._session.get(url, verify_ssl=False) as r:
            return await r.json()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def close(self) -> None:
        await self._session.close()


def load_config():
    '''加载配置文件'''
    if os.path.exists(f'{os.path.dirname(os.path.realpath(sys.argv[0]))}/config/config.json'):
        with open(f'{os.path.dirname(os.path.realpath(sys.argv[0]))}/config/config.json', 'r', encoding='utf-8') as fp:
            return json.loads(fp.read(), object_pairs_hook=OrderedDict)
    else:
        raise RuntimeError('未找到配置文件')


def get_most_opinion(case_id: str, opinions: list, username: str) -> list:
    '''获取最多观点'''
    opinion_statistics = {}
    for opinion in opinions:
        if opinion['vote'] in opinion_statistics:
            opinion_statistics[opinion['vote']] += 1
        else:
            opinion_statistics[opinion['vote']] = 1
    most_opinion = max(opinion_statistics, key=opinion_statistics.get)
    logging.debug(
        f'{username}：【{case_id}】的观点分布（观点id: 投票人数）{opinion_statistics}')
    return list(filter(lambda x: x['vote'] == most_opinion, opinions))


async def push(user: str,
               msgtpye: str,
               biliapi=None
               ):
    '''推送'''
    msg = {
        "CookieExpires": f"【风纪委员】\n{user}：cookie已过期！请重新获取！",
        "UnknownError": f"【风纪委员】\n{user}：发生未知错误！",
        "DailyMissions": None
    }
    if not configData["push"]["enable"] or msgtpye not in configData["push"]["msgtpye"]:  # 判断推送类型是否是用户填写的类型
        return
    elif msgtpye == "DailyMissions":
        jurylist = await biliapi.juryList()
        number = 0
        if jurylist['code'] == 0:
            for case in jurylist['data']['list']:
                if case['vote_time'] // (24 * 3600) == time.time() // (24 * 3600):  # 判断案件投票日期是否和脚本运行日期同一天，用于统计今日投票案件
                    number += 1
        else:
            logging.error(f'{user}：【推送】已投票案件获取失败')
            return
        msg['DailyMissions'] = f'【风纪委员】\n{user}：今日任务已完成{number}/20'

    '''企业微信推送'''
    if configData["push"]["wxpush"]["enable"]:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={configData["push"]["wxpush"]["corpid"]}&corpsecret={configData["push"]["wxpush"]["secret"]}'
            async with session.post(url) as response:
                if response.status == 200 and json.loads(await response.text())['errcode'] == 0:
                    access_token = json.loads(await response.text())['access_token']
                else:
                    logging.error(f'{user}：【企业微信推送】access_token获取失败')
                    return
            url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": configData["push"]["wxpush"]["touser"],
                "msgtype": "text",
                "agentid": configData["push"]["wxpush"]["agentid"],
                "text": {
                    "content": f"{msg.get(msgtpye)}"
                }
            }
            async with session.post(url, json=data) as response:
                if response.status == 200 and json.loads(await response.text())['errcode'] == 0:
                    logging.info(f'{user}：【企业微信推送】消息推送成功！')
                else:
                    logging.error(f'{user}：【企业微信推送】消息推送失败！')

    '''Telegram推送'''
    if configData["push"]["tgpush"]["enable"]:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            url = f'https://api.telegram.org/bot{configData["push"]["tgpush"]["bot_token"]}/sendMessage?chat_id={configData["push"]["tgpush"]["chat_id"]}&text={msg.get(msgtpye)}'
            async with session.get(url) as response:
                if response.status == 200:
                    logging.info(f'{user}：【Telegram推送】消息推送成功！')
                else:
                    logging.error(f'{user}：【Telegram推送】消息推送失败！')

    '''Server酱推送'''
    if configData["push"]["server"]["enable"]:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            url = f'https://sctapi.ftqq.com/{configData["push"]["server"]["sendkey"]}.send'
            data = {
                'title': '【风纪委员】',
                'desp': f"{msg.get(msgtpye)}"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logging.info(f'{user}：【Server酱推送】消息推送成功！')
                else:
                    logging.error(f'{user}：【Server酱推送】消息推送失败！')

    '''即时达推送'''
    if configData["push"]["ijingniu"]["enable"]:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            url = f'http://push.ijingniu.cn/send'
            data = {
                'channelkey': f'{configData["push"]["ijingniu"]["channelkey"]}',
                'msgHead': '【风纪委员】',
                'msgBody': f"{msg.get(msgtpye)}"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logging.info(f'{user}：【即时达推送】消息推送成功！')
                else:
                    logging.error(f'{user}：【即时达推送】消息推送失败！')

    '''pushplus推送'''
    if configData["push"]["pushplus"]["enable"]:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            url = f'http://www.pushplus.plus/send'
            data = {
                'token': f'{configData["push"]["pushplus"]["token"]}',
                'title': '【风纪委员】',
                'content': f"{msg.get(msgtpye)}"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logging.info(f'{user}：【pushplus推送】消息推送成功！')
                else:
                    logging.error(f'{user}：【pushplus推送】消息推送失败！')


async def opinion_vote(case_id: str,
                       opinions: list,
                       biliapi
                       ):
    '''观点投票'''
    vote_text_dict = {1: "合适", 2: "一般", 3: "不合适", 4: "无法判断", 11: "好", 12: "普通", 13: "差", 14: "无法判断"}
    try:
        most_opinion = get_most_opinion(
            case_id, opinions, biliapi.name)  # 获取最多观点
        opinion = random.choice(most_opinion)  # 从最多的观点里面随机选择一条
        try:
            opinion["vote_text"] = vote_text_dict[int(opinion["vote"])]
        except:
            pass
        logging.info(
            f'{biliapi.name}：为【{case_id}】选择了【{opinion["vote_text"]}】（{opinion["vote"]}）')
        vote = await biliapi.juryVote(case_id=case_id, vote=opinion['vote'])
        if vote["code"] == 0:
            logging.info(
                f'{biliapi.name}：成功根据【{opinion["uname"]}】的观点为案件【{case_id}】投下【{opinion["vote_text"]}】')
            return True
        else:
            logging.warning(
                f'{biliapi.name}：风纪委员投票失败，错误码：【{vote["code"]}】，信息为：【{vote["message"]}】')
            return False
    except Exception as er:
        logging.error(f'{biliapi.name}：发生错误，错误信息为：{er}')
        if _debug:
            traceback.print_exc()
        return False


async def replenish_vote(case_id: str,
                         biliapi,
                         default_vote: int
                         ):
    '''默认投票'''
    try:
        info = await biliapi.juryCaseInfo(case_id)
        if not info['code']:
            vote = await biliapi.juryVote(case_id=case_id, vote=info['data']['vote_items'][default_vote]['vote'])
            if vote["code"] == 0:
                logging.info(
                    f"{biliapi.name}：成功根据【配置文件】为案件【{case_id}】投下【{info['data']['vote_items'][default_vote]['vote_text']}】")
                return True
            else:
                logging.warning(
                    f'{biliapi.name}：风纪委员投票失败，错误码：【{vote["code"]}】，信息为：【{vote["message"]}】')
                return False
        else:
            logging.error(
                f'{biliapi.name}：获取风纪委员案件信息失败，错误码：【{info["code"]}】，信息为：【{info["message"]}】')
            return False
    except Exception as er:
        logging.error(f'{biliapi.name}：发生错误，错误信息为：{er}')
        if _debug:
            traceback.print_exc()
        return False


async def mode_1(biliapi,
                 default_vote: dict,
                 err: int = 3
                 ):
    while True:
        if err == 0:
            logging.error(f"{biliapi.name}：错误次数过多，结束任务！")
            await push(user=biliapi.name, msgtpye='UnknownError')
            return
        try:
            next_ = await biliapi.juryCaseObtain()  # 获取案件
            if next_["code"] == 0:
                case_id = next_['data']['case_id']
                opinions = await biliapi.juryopinion(case_id)  # 获取观点列表
                await biliapi.juryVote(case_id=case_id, vote=0)
                await asyncio.sleep(round(random.uniform(10, 20), 4))
                if opinions['data']['list']:
                    if not await opinion_vote(case_id, opinions['data']['list'], biliapi):
                        err -= 1
                else:
                    if not await replenish_vote(case_id, biliapi, random.choice(default_vote['vote'])):
                        err -= 1
            elif next_["code"] == 25014:  # 案件已审满
                logging.info(f'{biliapi.name}：{next_["message"]}')
                return
            elif next_["code"] == 25008:  # 没有新案件
                logging.info(f'{biliapi.name}：{next_["message"]}')
                if default_vote['once']:
                    logging.info(f'{biliapi.name}：休眠30分钟后继续获取案件！')
                    await asyncio.sleep(1800)
                else:
                    return
            elif next_["code"] == 25006:  # 风纪委员资格已过期
                logging.warning(f'{biliapi.name}：风纪委员资格已过期，尝试申请资格')
                r = await biliapi.juryapply()
                if r["code"] != 0:
                    logging.info(f'{biliapi.name}：{r}')
                    return
            else:
                logging.warning(
                    f'{biliapi.name}：获取风纪委员案件失败，错误码：【{next_["code"]}】，信息为：【{next_["message"]}】')
                err -= 1
                await asyncio.sleep(round(random.uniform(20, 40), 4))
        except Exception as er:
            logging.error(f'{biliapi.name}：发生错误，错误信息为：{er}')
            if _debug:
                traceback.print_exc()
            err -= 1
            await asyncio.sleep(round(random.uniform(20, 40), 4))


async def mode_2(biliapi,
                 default_vote: dict,
                 err: int = 3
                 ):
    case_id_list = []
    while True:
        if err == 0:
            logging.error(f"{biliapi.name}：错误次数过多，结束任务！")
            await push(user=biliapi.name, msgtpye='UnknownError')
            return
        try:
            next_ = await biliapi.juryCaseObtain()  # 获取案件
            if next_["code"] == 0:
                case_id = next_['data']['case_id']
                opinions = await biliapi.juryopinion(case_id)  # 获取观点列表
                await biliapi.juryVote(case_id=case_id, vote=0)
                await asyncio.sleep(round(random.uniform(10, 20), 4))
                if opinions['data']['list']:
                    if not await opinion_vote(case_id, opinions['data']['list'], biliapi):
                        err -= 1
                else:
                    case_id_list.append(case_id)
            elif next_["code"] == 25014:  # 案件已审满
                logging.info(f'{biliapi.name}：{next_["message"]}')
                return
            elif next_["code"] == 25008:  # 没有新案件
                logging.info(f'{biliapi.name}：{next_["message"]}')
                if not case_id_list and default_vote['once']:
                    logging.info(f'{biliapi.name}：休眠30分钟后继续获取案件！')
                    await asyncio.sleep(1800)
                else:
                    for case_id in case_id_list:
                        case_id_list.remove(case_id)
                        if err == 0:
                            logging.error(f"{biliapi.name}：错误次数过多，结束任务！")
                            return
                        if not await replenish_vote(case_id, biliapi, random.choice(default_vote['vote'])):
                            err -= 1
                        await asyncio.sleep(round(random.uniform(10, 20), 4))
            elif next_["code"] == 25006:  # 风纪委员资格已过期
                logging.warning(f'{biliapi.name}：风纪委员资格已过期，尝试申请资格')
                r = await biliapi.juryapply()
                if r["code"] != 0:
                    logging.info(f'{biliapi.name}：{r}')
                    return
            else:
                logging.warning(
                    f'{biliapi.name}：获取风纪委员案件失败，错误码：【{next_["code"]}】，信息为：【{next_["message"]}】')
                err -= 1
                await asyncio.sleep(round(random.uniform(20, 40), 4))
        except Exception as er:
            logging.error(f'{biliapi.name}：发生错误，错误信息为：{er}')
            if _debug:
                traceback.print_exc()
            err -= 1
            await asyncio.sleep(round(random.uniform(20, 40), 4))


async def start(user: dict,
                configData: dict,
                ):
    '''开始投票'''
    async with asyncBiliApi(configData["http_header"]) as biliapi:
        try:
            if not await biliapi.login_by_cookie(user["cookieDatas"]):
                logging.error(
                    f'id为【{user["cookieDatas"]["DedeUserID"]}】的账户cookie失效，跳过此账户后续操作')
                await push(user=user["cookieDatas"]["DedeUserID"], msgtpye='CookieExpires')
                return
        except Exception as er:
            logging.error(
                f'登录验证id为【{user["cookieDatas"]["DedeUserID"]}】的账户失败，原因为【{er}】，跳过此账户后续操作')
            await push(user=user["cookieDatas"]["DedeUserID"], msgtpye='UnknownError')
            if _debug:
                traceback.print_exc()
            return
        try:
            logging.info(f'{biliapi.name}：开始执行风纪委员投票！')
            if configData['default_vote']['mode'] == 1:
                await mode_1(biliapi, configData['default_vote'])
            elif configData['default_vote']['mode'] == 2:
                await mode_2(biliapi, configData['default_vote'])
            await push(user=user["cookieDatas"]["DedeUserID"], msgtpye='DailyMissions', biliapi=biliapi)
        except Exception as er:
            logging.error(f'{biliapi.name}：发生错误，错误信息为：{er}')
            await push(user=user["cookieDatas"]["DedeUserID"], msgtpye='UnknownError')
            if _debug:
                traceback.print_exc()
            return


async def main(configData):
    await asyncio.wait([asyncio.ensure_future(start(user=user, configData=configData)) for user in configData["users"]])


if __name__ == '__main__':
    try:
        logging.basicConfig(
            level=logging.INFO, format="[%(asctime)s] [%(levelname)s]: %(message)s")
        configData = load_config()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(configData))
    except Exception as er:
        logging.error(f'配置加载异常，原因为{er}，退出程序')
        if _debug:
            traceback.print_exc()
    # if platform.system().lower() == 'windows':  # 用户反应windows运行源代码时可能出现奇怪的问题
    if sys.argv[0].split('.')[-1] == 'exe':  # 故使用粗暴方式判断
        import msvcrt

        logging.info("按任意键退出")
        ord(msvcrt.getch())
    sys.exit()
