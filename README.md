# edX Membership

The goal of this project is to make learner can subscribe VIP membership of any online courses learning platform set up by using edx-platfrom, and learn freely instead of buying the courses one by one.

## Getting Start

依赖库
- [edx-platform](https://github.com/e-ducation/edx-platform.git)
- [eliteu-payments](https://github.com/e-ducation/eliteu-payments)

更新 lms.env.json，在 FEATURES 里加上以下字段
```json
"FEATURE": {
    "ENABLE_MEMBERSHIP_INTEGRATION": true,
    "ENABLE_PAYMENTS_INTEGRATION": true,
    "ENABLE_COURSE_UNENROLL": true,
}
```


devstack 环境配置
修改 devstack/docker-compose-host.yml
```yml
services:
  lms:
    volumes:
      - ${DEVSTACK_WORKSPACE}/edx-platform:/edx/app/edxapp/edx-platform:cached
      - edxapp_node_modules:/edx/app/edxapp/edx-platform/node_modules
      - ${DEVSTACK_WORKSPACE}/src:/edx/src:cached
      - ${DEVSTACK_WORKSPACE}/edx-membership:/edx/app/edxapp/edx-membership:cached
      - ${DEVSTACK_WORKSPACE}/eliteu-payments:/edx/app/edxapp/eliteu-payments:cached
```

重启 docker
- 执行 make dev.up
- 执行 make lms-logs 查看启动情况
    > 若干log 出现报错，尝试执行 make lms-shell 进入 lms 环境，再依次执行 make clean 和 make requirements;退出 lms 环境，执行 make lms-static


修改 /edx/app/edxapp/lms.auth.json 添加支付配置
```json
{
    "ALIPAY_INFO": {
        "basic_info": {
            "KEY": "******", 
            "PARTNER": "*******", 
            "SELLER_EMAIL": "xxx@xxx.com"
        }, 
        "other_info": {
            "INPUT_CHARSET": "utf-8", 
            "INPUT_DIRECT_CHARSET": "gbk", 
            "SIGN_TYPE": "", 
            "RETURN_URL": "http://example.com/api/v1/payments/alipay/alipaysuccess/", 
            "NOTIFY_URL": "http://example.com/api/v1/payments/alipay/alipayasyncnotify/", 
            "PAY_RESULT_URL": "http://example.com/vip/card", 
            "REFUND_NOTIFY_URL": "http://example.com/shoppinglist/alipay/alipayrefundasyncnotify", 
            "SHOW_URL": "", 
            "ERROR_NOTIFY_URL": "http://example.com/shoppinglist/alipay/errornotify/", 
            "TRANSPORT": "https", 
            "DEFAULT_BANK": "CITIC-DEBIT", 
            "IT_B_PAY": "2d", 
            "REFUND_URL": "refund_fastpay_by_platform_pwd"
        }
    }, 
    "ALIPAY_APP_INFO": {
        "basic_info":{
            "APP_ID": "***********",
            "APP_PRIVATE_KEY": "path_to_app_private_key.pem",
            "ALIPAY_RSA_PUBLIC_KEY": "path_to_alipay_public_key.pem"
        },
        "other_info":{
            "SIGN_TYPE": "RSA",
            "NOTIFY_URL": "http://example.com/api/v1/payments/alipay/app_alipayasyncnotify/"
        }
    },
    "WECHAT_APP_PAY_INFO": {
        "basic_info": {
            "APPID": "********",
            "APPSECRET": "*******",
            "MCHID": "******",
            "KEY": "******",
            "ACCESS_TOKEN": "******"
        },
        "other_info": {
            "NOTIFY_URL": "http://xxxxx"
        }
    },
    "WECHAT_PAY_INFO": {
        "basic_info": {
            "APPID": "********", 
            "APPSECRET": "*********", 
            "MCHID": "*******", 
            "KEY": "*********", 
            "ACCESS_TOKEN": "********"
        }, 
        "other_info": {
            "BUY_COURSES_SUCCESS_TEMPLATE_ID": "", 
            "BUY_COURSES_SUCCESS_HREF_URL": "", 
            "COIN_SUCCESS_TEMPLATE_ID": "-EIRCM8X55ae7H2bZM0AYhRR-Q", 
            "COIN_SUCCESS_HREF_URL": "", 
            "SERVICE_TEL": "", 
            "NOTIFY_URL": "http://example.com/api/v1/payments/wechat/wechatasyncnotify/", 
            "JS_API_CALL_URL": "", 
            "SSLCERT_PATH": "path_to_apiclient_cert.pem", 
            "SSLKEY_PATH": "path_to_apiclient_key.pem"
        }
    },
}
```

安装依赖库
```bash
cd /edx/app/edxapp/edx-membership
pip install -r requirements/base.txt

cd /edx/app/edxapp/eliteu-payments
pip install -r requirements/base.txt
```

同步数据库
```bash
sudo -H -u edxapp bash
source ../edxapp_env 
python /edx/app/edxapp/edx-platform/manage.py lms --settings devstack_docker makemigrations membership
python /edx/app/edxapp/edx-platform/manage.py lms --settings devstack_docker migrate membership
```

更新静态资源
```bash
apt-get install sass
cd /edx/app/edxapp/edx-membership
sudo sass --update membership/static/membership/sass/:membership/static/membership/css/ -E "UTF-8"
sudo -H -u edxapp bash
source ../edxapp_env 
paver update_assets --settings=aws
```

重启服务
```bash
/edx/bin/supervisorctl restart all
```


## How to Contribute
Visit the [Contributor Guidelines](https://github.com/e-ducation/edx-membership/blob/master/CONTRIBUTING.md) for details on how to contribute as well as the [Open Code of Conduct](https://github.com/e-ducation/edx-membership/blob/master/CODE_OF_CONDUCT.md) for details on how to participate.


## Reporting Security Issues
Please do not report security issues in public. Please email code@e-ducation.cn.

## License
This project is licensed under the AGPL Version 3.0 License.
See the [LICENSE](https://github.com/e-ducation/edx-membership/blob/master/LICENSE) file for the full license text.
