## 介绍
- 本项目能够解决 [immersive translater](https://immersivetranslate.com/en/) 的
使用 openai 翻译时存在的问题。
    >免责声明，这些都是我个人认为存在的问题
  1. 希望采用上下文的多段落翻译时，因 LLM 翻译固有的问题，不能 100% 返回原始段落数量
  2. 不能在使用 openai 翻译的时候，同时需要为某些特殊的段落使用其他翻译引擎
- 能够使用 web gpt 逆向
- 能够将其他 llm 引擎中转至 openai，多为 openai 的单一调用

## 原理
本包是通过 selenium 获取token，一劳永逸

## 安装
```bash
git clone git@github.com:witsir/TranslateGuard.git
#切换至 pyproject.toml 所在目录 
cd TranslateGuard
pip install -e .
```

## 使用
```bash
# 进入子目录,创建 .env 文件保存 你的EMAIL和PASSWORD
cd TranslateGuard
python -venv venv
source venv/bin/activate
python -m TranslateGuard
```

