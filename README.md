# External Imagegen Skill for Codex

让 Codex 通过你自己的 OpenAI 兼容生图 API 生成图片，而不依赖 Codex 内置生图工具。

## 支持范围

- 调用 `POST <IMAGE_API_BASE_URL>/images/generations`
- 支持 API 返回 `data[0].b64_json` 或 `data[0].url`
- 图片只能保存到当前项目目录内
- 外部 API 失败时停止，不自动回退其他生图服务
- 当前仅支持文生图，不包含图片编辑或蒙版

## 安装

```bash
git clone https://github.com/warm-1/external-imagegen-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R external-imagegen-skill/external-imagegen \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

新建 Codex 任务。如果 Skill 没有出现在列表中，重启 Codex。

## 配置 API

API 必须兼容 OpenAI Images API。`IMAGE_API_BASE_URL` 通常以 `/v1` 结尾：

```bash
export IMAGE_API_BASE_URL="https://api.example.com/v1"
export IMAGE_API_KEY="your-api-key"
export IMAGE_MODEL="your-image-model"
```

不要把真实 Key 写入仓库、`SKILL.md`、`AGENTS.md` 或提交记录。Codex Desktop 必须从能够继承这些环境变量的启动环境运行；修改变量后请重新启动 Codex。

可先确认服务端模型：

```bash
curl "$IMAGE_API_BASE_URL/models" \
  -H "Authorization: Bearer $IMAGE_API_KEY"
```

## 让 Codex 自动调用

在 `~/.codex/AGENTS.md` 添加：

```md
#### 外部生图路由
* 所有生成、绘制、渲染或创建位图的请求，必须使用 `external-imagegen` Skill。
* 禁止使用 Codex 内置生图工具或其他生图服务；外部 API 失败时，报告错误并停止，不得静默回退。
```

之后直接对 Codex 说：

```text
生成一张赛博朋克风格的咖啡产品海报，保存到 outputs/coffee-poster.png
```

也可以显式调用：

```text
$external-imagegen 生成一张 16:9 的科技视频封面
```

## 手动调用

在目标项目目录执行：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/external-imagegen/scripts/generate_image.py" \
  --prompt "A cinematic product photo of a ceramic coffee mug" \
  --output "outputs/coffee-mug.png" \
  --size "1024x1024"
```

成功时输出：

```text
IMAGE_SAVED=/absolute/path/to/outputs/coffee-mug.png
```

## 测试

```bash
python3 -m unittest discover -s external-imagegen/tests -v
```

## License

MIT
