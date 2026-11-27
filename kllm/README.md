# kLLM 样例

本目录收录 kLLM 视频生成（MiniMax H3）样例的清单、方案说明、预设对比记录与对照页面生成器。视频文件本身存放在本仓库的发布页面，不进入 Git 历史。

| 路径 | 内容 |
|---|---|
| [`samples/manifest.json`](samples/manifest.json) | 样例清单：每个文件的发布位置（`release`、`url`）、SHA-256、样例集、系列、方案编号或分组、画幅、种子、分辨率、时长、大小、实测耗时、显存与主机内存峰值、GPU 型号与说明 |
| [`samples/comparisons.json`](samples/comparisons.json) | 预设对比记录：同一用例下需要并排查看的样例组合 |
| [`schemes.md`](schemes.md) | 方案说明：A、B、H 系列与官方工作流的公开编号、用途，以及每个方案已发布样例的实测数据与下载链接 |
| [`tools/build_page.py`](tools/build_page.py) | 对照页面生成器：把清单与对比记录合并为一份数据，用访问密钥加密后写入页面 |
| [`tools/page.html`](tools/page.html) | 对照页面模板：输入访问密钥后在浏览器内解密，提供按系列浏览、同步并排播放与全部样例表 |

## 发布

| 发布 | 内容 |
|---|---|
| [`kllm-samples`](https://github.com/ANetResearch/ANet-Entertainment/releases/tag/kllm-samples) | 既有测试报告中的样例，原样文件 |
| [`kllm-rc4-runs`](https://github.com/ANetResearch/ANet-Entertainment/releases/tag/kllm-rc4-runs) | 0.2.9-rc.4 开发构建的全部实测出片，持续追加 |

后续版本的实测出片以新的发布追加，命名方式相同（例如 `kllm-rc5-runs`），并登记在同一份清单中。

## 校验

下载的文件可按清单中的 `sha256` 字段校验，例如：

```sh
sha256sum rc4-a59-portrait-s42-01.mp4
```

## 对照页面

页面地址为 <https://anetresearch.github.io/ANet-Entertainment/>，需访问密钥。页面中的全部对照数据（样例列表、视频地址、实测数据与说明）以 PBKDF2-SHA256（600,000 次迭代）派生的密钥经 AES-256-GCM 加密，浏览器在输入密钥后用 WebCrypto 解密；未输入密钥时页面只显示密钥输入框。密钥可选择记在本浏览器中，并可随时清除。

生成页面：

```sh
python3 kllm/tools/build_page.py --manifest kllm/samples/manifest.json \
    --comparisons kllm/samples/comparisons.json --key-file <访问密钥文件> --out <输出目录>/index.html
```

生成器需要 Python 3.8 及以上版本与 `cryptography` 包。
