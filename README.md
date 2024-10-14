# 我在校园自动签到工具之江西制造职业技术学院

该项目基于 [NewWoZaiXiaoYuan](https://github.com/LinChiQ/NewWoZaiXiaoYuan) 进行了二次修改，适用于**江西制造职业技术学院**的自动签到和登录系统,并未适配其他功能



## 功能说明

- 自动登录并签到我在校园平台
- 支持定制的地理位置信息（经纬度等）
- 支持将 JWSESSION 存入本地文件，以便下次自动登录
- 支持多用户签到

## 环境要求

- Python 3.x
- pip（用于安装依赖项）

## 配置文件说明

使用前需要在项目根目录下创建一个 `config.json` 配置文件，配置你的账号和地理位置。以下是配置文件的结构示例：

```json
{
    "users": [
        {
            "name": "张三",
            "school_name": "学校名称",
            "username": "账号",
            "password": "密码",
            "location": {
                "latitude": "28.682892",
                "longitude": "115.858197",
                "country": "中国",
                "province": "江西",
                "city": "南昌",
                "district": "青山湖区",
                "street": "紫阳大道318号"
            },
            "JWSESSION": ""
        },
        {
            "name": "",
            "school_name": "",
            "username": "",
            "password": "",
            "location": {
                "latitude": "28.682892",
                "longitude": "115.858197",
                "country": "中国",
                "province": "江西",
                "city": "南昌",
                "district": "青山湖区",
                "street": "紫阳大道318号"
            },
            "JWSESSION": ""
        }
    ]
}
```



### 配置项说明

- **school_name**: 学校名称。

- **username**: 我在校园的登录账号。

- **password**: 我在校园的登录密码，建议使用字母和数字的组合。

- location

  : 包含经纬度和具体地址，用于签到时模拟位置。

  - `latitude`: 纬度（例如 28.6838）
  - `longitude`: 经度（例如 115.858）
  - `country`: 国家，填写为 `"中国"`。
  - `province`: 省份，填写为 `"江西省"`。
  - `city`: 城市，填写为 `"南昌市"`。
  - `district`: 区，填写为 `"南昌县"`。
  - `street`: 街道，填写为 `"紫阳大道318号"`。

- **JWSESSION**: 登录成功后，程序会自动将 JWSESSION 存入此字段，用于后续的自动登录。

## 使用说明

1. **账号和密码设置**:
   请将你的我在校园账号和密码正确填写在 `config.json` 文件中。**密码必须包含字母和数字的组合**，否则程序登录可能失败。
2. **首次运行**:
   运行程序时，程序会尝试自动登录，并将生成的 JWSESSION 存储在 `config.json` 文件中。之后，程序会使用该 JWSESSION 进行自动签到和操作。
3. **密码修改后的处理**:
   - 如果你修改了我在校园的登录密码，请务必点击清除缓存，等待页面跳转到未登录界面。
   - 此时，将新密码填入 `config.json` 文件中，然后重新运行程序。
4. **自动签到**:
   程序会使用配置的经纬度等信息进行自动签到，并记录操作结果。

## 安装依赖

在项目目录下，运行以下命令安装依赖：在项目目录下，运行以下命令安装依赖：

```bash
pip install -r requirements.txt
```

## 运行项目

在终端中执行以下命令启动程序：

```bash
python main.py
```
