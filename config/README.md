```json5
{
    "http_header": {  // 建议使用常用浏览器的ua
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
        "Connection": "keep-alive"
    },
    "default_vote": {  // 默认投票
        "mode": 1,  // 选择模式，1为获取案件后有观点就参考观点，没有就投默认，2为获取案件后有观点就参考观点，没有就先暂存案件id跳过，等案件池空了获取不到观点后再倒回去投默认
        "vote": [0, 1],  // 默认投票，0为好，1为普通，2为差，3为无法判断,填多个为随机投票，填一个为固定投票
        "once": true  // true为审满案件后退出，false为获取不到新案件后退出
    },
    "users": [
        {
            "cookieDatas": {  // 账号一
                "SESSDATA": "xxxxx",
                "bili_jct": "xxxxx",
                "DedeUserID": "xxxxx"
            }
        },
        {
            "cookieDatas": {  // 账号二
                "SESSDATA": "xxxxx",
                "bili_jct": "xxxxx",
                "DedeUserID": "xxxxx"
            }
        }
    ],
    "push": {  // 推送
        "enable": false,  // 开关，false或0为关闭所有推送，true或1为开启所有推送
        "msgtpye": ["CookieExpires", "UnknownError", "DailyMissions"],  // 选择推送类型，"CookieExpires"为cookie过期推送，"UnknownError"为运行报错推送，"DailyMissions"为每日任务完成状况推送
        "wxpush": {  // 企业微信推送必填，获取方法自行搜索
            "enable": false,  // 开关，false或0为关闭企业微信推送，true或1为开启企业微信推送
            "corpid": "xxxxx",  // 企业id，字符串类型
            "secret": "xxxxx",  // 应用密钥，字符串类型
            "agentid": 1000001,  // 应用id，数字整型
            "touser": "@all"  // 指定接收消息的成员，在企业微信网页-通讯录-成员详情-账号，成员ID列表（多个接收者用‘|’分隔，最多支持1000个）。特殊情况：指定为"@all"，则向该企业应用的全部成员发送
        },
        "tgpush": {  // Telegram推送必填，获取方法自行搜索
            "enable": false,  // 开关，false或0为关闭TG推送，true或1为开启TG推送
            "bot_token": "xxxxx:xxxxx", // 私聊@BotFather获取的机器人token
            "chat_id": "-100xxxxx" // 指定接收消息的用户/频道/群组id，频道或群组需要在开头加上"-100"
        }
    }
}
```