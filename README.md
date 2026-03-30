# Cross Over The Wall

使用singbox去做v2ray的订阅地址解析

## 快速开始

### 1. 下载依赖
```bash
./download.sh
```

### 2. 配置订阅地址

复制示例配置文件并修改：
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的订阅地址
```

或通过命令行参数直接传入：
```bash
python update_singbox.py --sub-url <订阅地址>
```

### 3. 更新并启动
```bash
python update_singbox.py
./start.sh
```

## 配置说明

- `config.json.tmpl`: 配置模板文件
- `config.json`: 实际运行配置文件（自动生成，已加入 gitignore）
- `.env.example`: 环境变量示例文件
- `.env`: 环境变量配置文件（从 .env.example 复制，已加入 gitignore）

## 默认端口

- http+socks4+socks4a+socks5: 10808
