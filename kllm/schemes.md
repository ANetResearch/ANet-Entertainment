# kLLM 方案说明

本文按系列列出 kLLM 视频生成（MiniMax H3）的公开方案编号、用途说明，以及每个方案已发布样例的实测数据与下载链接。
系列按底模划分：A 系列以 INT8 为底模，B 系列以 BF16 为底模，H 系列以混合权重为底模；每个系列内都可以是剪枝、量化或原始权重，并可选 LoRA、加速与 EasyCache。
官方工作流指 MiniMax H3 官方参考生成视频工作流在 kLLM 上运行。耗时为端到端（提交到取回成片）；显存峰值为整卡已用显存；主机内存峰值为进程或容器内存。数据由同步脚本根据 `samples/manifest.json` 生成。

## 方案组件一览

组件按 kLLM 0.2.9 中各方案的配置列出，不含采样参数。底模注明“参考生视频版”者为 MiniMax H3 官方发布的另一种底模变体，未注明者为默认变体；混合权重以默认变体为主，部分层取自参考生视频版。加速 LoRA 为减少采样计算量的适配权重，turbo 系列单独注明；其他 LoRA 按用途列出。EasyCache 为相邻采样步之间的计算复用，只在实际生效的方案中列出。Sol 稀疏注意力为块稀疏注意力。两遍生成（潜空间放大）指先在较小画布上生成，在潜空间放大后再细化。RelayVSR ×2 超分为成片的 2 倍视频超分辨率。除注明外，文本编码器为 INT8。分辨率为方案支持的输出档位。官方工作流的加速配置随版本变化，未列出。

| 编号 | 系列 | 组件 |
|---|---|---|
| A01 | A 系列 | 混合权重底模（INT8） · 加速 LoRA · 其他 LoRA（打斗动作、动作连续性修复、电影质感） · 两遍生成（同分辨率） · NVFP4 文本编码器 · 480p、768p |
| A02 | A 系列 | INT8 剪枝底模（参考生视频版） · 加速 LoRA · EasyCache · 单遍生成 · NVFP4 文本编码器 · 480p、768p |
| A03 | A 系列 | INT8 剪枝底模（参考生视频版） · 加速 LoRA · EasyCache · 单遍生成 · NVFP4 文本编码器 · 480p、768p |
| A04 | A 系列 | INT8 剪枝底模（参考生视频版，社区微调） · 加速 LoRA · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| A05 | A 系列 | INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| A57 | A 系列 | — |
| A58 | A 系列 | INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 1080p、2K |
| A59 | A 系列 | INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · RelayVSR ×2 超分 · 输出 1536p（由 768p 超分） |
| B00 | B 系列 | BF16 原始底模（参考生视频版） · 不使用 LoRA · 单遍生成 · 480p、768p |
| B01 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B02 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B03 | B 系列 | BF16 原始底模（参考生视频版） · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B04 | B 系列 | BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B05 | B 系列 | BF16 原始底模（参考生视频版） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B06 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo 完整版） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B07 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo 完整版） · 其他 LoRA（电影感、动作连续性修复） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B08 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo 与另一种） · 其他 LoRA（电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B09 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（徒手打斗、打斗动作、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B10 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（武术动作、打斗动作、动作连续性修复、武术空间物理） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B11 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（动作与打斗推理、兵器速度、冲击反馈、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B12 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（动作增强、镜头运动、面部表情与口型、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B13 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（写实人物、写实度调节、电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B14 | B 系列 | BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B15 | B 系列 | BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B16 | B 系列 | BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（社区风格） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B17 | B 系列 | BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B54 | B 系列 | INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| B55 | B 系列 | BF16 原始底模 · 不使用 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · BF16 文本编码器 · 480p、768p、960p |
| B59 | B 系列 | BF16 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 768p |
| B60 | B 系列 | BF16 剪枝底模 · 不使用 LoRA · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 768p |
| B61 | B 系列 | BF16 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · RelayVSR ×2 超分 · 输出 1536p（由 768p 超分） |
| H02 | H 系列 | 混合权重底模（BF16） · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| H04 | H 系列 | 混合权重底模（BF16） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| H05 | H 系列 | 混合权重底模（BF16） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| H06 | H 系列 | 混合权重底模（BF16） · 加速 LoRA（turbo 完整版） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| H08 | H 系列 | 混合权重底模（BF16） · 加速 LoRA（turbo 与另一种） · 其他 LoRA（电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p |
| H55 | H 系列 | 混合权重底模（BF16） · 不使用 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · BF16 文本编码器 · 480p、768p、960p |
| 官方 BF16 | 官方工作流 | BF16 原始底模（参考生视频版） · 不使用 LoRA · 单遍生成 |
| 官方 INT8 | 官方工作流 | INT8 底模（参考生视频版） · 不使用 LoRA · 单遍生成 |

## A 系列

以 INT8 为底模。

### A01

社区工作流：多图多音参考，兼顾动作与对白。

组件：混合权重底模（INT8） · 加速 LoRA · 其他 LoRA（打斗动作、动作连续性修复、电影质感） · 两遍生成（同分辨率） · NVFP4 文本编码器 · 480p、768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A01 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a01-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 17 分 52 秒 | 24.1 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A01 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a01-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 16 分 34 秒 | 21.4 GiB | 38.8 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A01 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a01-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 16 分 36 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A01 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a01-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 16 分 36 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A01 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a01-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A01 · 768p 竖屏 · 5 秒 · 种子 42 · 含首次加载](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a01-768p-portrait-5s-first.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 768×1344 | 5.17 秒 | 5 分 42 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### A02

社区工作流：多图多音参考。

组件：INT8 剪枝底模（参考生视频版） · 加速 LoRA · EasyCache · 单遍生成 · NVFP4 文本编码器 · 480p、768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A02 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a02-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 22 分 46 秒 | 26.0 GiB | 38.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A02 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a02-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 21 分 13 秒 | 22.1 GiB | 39.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A02 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a02-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 21 分 27 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A02 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a02-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 21 分 21 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A02 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a02-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### A03

社区工作流：多图参考，不接受音频输入。

组件：INT8 剪枝底模（参考生视频版） · 加速 LoRA · EasyCache · 单遍生成 · NVFP4 文本编码器 · 480p、768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A03 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a03-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 19 分 13 秒 | 26.1 GiB | 39.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A03 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a03-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 19 分 04 秒 | 22.0 GiB | 39.8 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A03 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a03-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 19 分 11 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A03 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a03-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 19 分 10 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A03 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a03-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### A04

社区工作流：多图多音参考，高速。

组件：INT8 剪枝底模（参考生视频版，社区微调） · 加速 LoRA · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A04 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a04-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 8 分 52 秒 | 29.9 GiB | 47.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A04 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a04-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 7 分 37 秒 | 29.9 GiB | 47.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A04 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a04-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 7 分 43 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A04 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a04-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 7 分 43 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A04 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a04-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### A05

社区工作流：多图多音参考，高速；A 系列高清与超分方案均以其链路为基础。

组件：INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A05 · 960p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 960×1728 | 15.08 秒 | 15 分 43 秒 | 28.6 GiB | 55.8 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 11 分 26 秒 | 28.2 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-02.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 50 秒 | 30.6 GiB | 54.1 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-03.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 37 秒 | 30.6 GiB | 55.4 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-04.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 37 秒 | 30.6 GiB | 54.9 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-05.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 37 秒 | 30.6 GiB | 52.1 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-06.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 43 秒 | 23.7 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-07.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 14 分 14 秒 | 28.2 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 960p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-08.mp4) | 0.2.9-rc.4 实测出片 | 960×1728 | 15.08 秒 | 15 分 49 秒 | 28.6 GiB | 55.4 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-09.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 8 分 31 秒 | 26.1 GiB | 51.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-10.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 8 分 46 秒 | 26.1 GiB | 53.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a05-portrait-s42-11.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 8 分 34 秒 | 26.1 GiB | 51.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 原生 1080p 竖屏 · 15 秒 · 种子 20261126 · 新编码](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-1080p-enc2-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 1088×1920 | 15.08 秒 | 22 分 28 秒 | 24.4 GiB | 57.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 原生 1080p 竖屏 · 15 秒 · 种子 42 · 新编码](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-1080p-enc2-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1088×1920 | 15.08 秒 | 22 分 31 秒 | 24.4 GiB | 55.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 原生 1080p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-1080p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1920×1088 | 15.08 秒 | 22 分 31 秒 | 24.4 GiB | 55.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 原生 1080p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-1080p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1088×1920 | 15.08 秒 | 24 分 08 秒 | 25.5 GiB | 55.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 原生 2K 竖屏 · 15 秒 · 种子 42 · 新编码](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-2k-enc2-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1440×2560 | 15.08 秒 | 61 分 47 秒 | 29.7 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 原生 2K 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-2k-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1440×2560 | 15.08 秒 | 61 分 57 秒 | 29.7 GiB | 54.1 GiB | NVIDIA RTX 4080 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42 · 新编码](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-enc2-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 8 分 31 秒 | 26.1 GiB | 54.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 20261126 · 提示词：编译服务补全镜头语言](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-prompt-compiled-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 9 分 37 秒 | 26.1 GiB | 55.4 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42 · 提示词：编译服务补全镜头语言](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-prompt-compiled-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 9 分 37 秒 | 26.1 GiB | 55.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42 · 提示词：编译服务加固定风格预设](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-prompt-compiled-style-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 9 分 31 秒 | 26.1 GiB | 55.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 20261126 · 提示词：用户自然语言](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-prompt-plain-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 9 分 13 秒 | 25.9 GiB | 54.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42 · 提示词：用户自然语言](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-a05-768p-prompt-plain-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 9 分 07 秒 | 25.9 GiB | 55.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 15 秒](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a05-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 8 分 49 秒 | 30.6 GiB | 48.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-a05-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 8 分 40 秒 | 30.6 GiB | 47.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 480p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a05-480p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 864×480 | 15.08 秒 | 3 分 28 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 480p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a05-480p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 480×864 | 15.08 秒 | 3 分 48 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a05-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 8 分 43 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-a05-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 8 分 47 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求，2 张参考图、1 段音频](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-landscape-5s-compact-few.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求，参考素材为 https 地址](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-landscape-5s-compact-https.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 5 秒 · 种子 42 · 在 A01 之后运行，含切换](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-portrait-5s-after-a01.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 768×1344 | 5.17 秒 | 4 分 28 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 5 秒 · 种子 42 · 调用说明样例，5 张参考图、无音频](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-portrait-5s-sample.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 768×1344 | 5.17 秒 | 3 分 59 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 5 秒 · 种子 42 · 交付镜像冒烟测试](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-portrait-5s-smoke.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 768×1344 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 竖屏 · 5 秒 · 种子 42 · 热态重复](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-a05-768p-portrait-5s-warm.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 768×1344 | 5.17 秒 | 3 分 25 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [A05 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/v028-a05-768p-landscape.mp4) | 0.2.8 调用样例 | 1344×768 | 15.08 秒 | 10 分 29 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### A57

测试构建，未发布：A05 链路加 BF16 LoRA 的试验方案。

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A57 · 768p 横屏 · 15 秒 · 种子 42 · 首次运行，含模型组切换与 LoRA 合并](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/test-a57-768p-landscape-cold.mp4) | A57 测试构建 | 1344×768 | 15.08 秒 | 19 分 07 秒 | 29.3 GiB | 45.8 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A57 · 768p 横屏 · 15 秒 · 种子 42 · 热态，9 张参考图](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/test-a57-768p-landscape-warm-9pics.mp4) | A57 测试构建 | 1344×768 | 15.08 秒 | 15 分 21 秒 | 24.3 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A57 · 768p 横屏 · 15 秒 · 种子 42 · 热态](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/test-a57-768p-landscape-warm.mp4) | A57 测试构建 | 1344×768 | 15.08 秒 | 14 分 43 秒 | 28.3 GiB | 47.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A57 · 768p 竖屏 · 15 秒 · 种子 42 · 热态](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/test-a57-768p-portrait-warm.mp4) | A57 测试构建 | 768×1344 | 15.08 秒 | 14 分 47 秒 | 28.3 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [A57 · 768p 竖屏 · 15 秒 · 种子 42 · 热态重复](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/test-a57-768p-portrait-warm2.mp4) | A57 测试构建 | 768×1344 | 15.08 秒 | 14 分 51 秒 | 23.9 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### A58

A05 链路的原生高清：1080p（输出 1088×1920 或 1920×1088）与 2K（输出 1440×2560 或 2560×1440）。

组件：INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 1080p、2K

暂无已发布样例。

### A59

A05 生成 768p 后做 2 倍超分辨率（输出 1536×2688 或 2688×1536）。

组件：INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · RelayVSR ×2 超分 · 输出 1536p（由 768p 超分）

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [A59 · 1536p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a59-landscape-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 2688×1536 | 15.08 秒 | 11 分 01 秒 | 23.7 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A59 · 1536p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a59-landscape-s42-02.mp4) | 0.2.9-rc.4 实测出片 | 2688×1536 | 15.08 秒 | 10 分 16 秒 | 30.6 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A59 · 1536p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a59-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 1536×2688 | 15.08 秒 | 11 分 21 秒 | 23.7 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [A59 · 1536p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-a59-portrait-s42-02.mp4) | 0.2.9-rc.4 实测出片 | 1536×2688 | 15.08 秒 | 10 分 26 秒 | 30.6 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |

## B 系列

以 BF16 为底模。

### B00

官方 BF16 工作流的编号版本，按统一请求调用。

组件：BF16 原始底模（参考生视频版） · 不使用 LoRA · 单遍生成 · 480p、768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B00 · 768p 竖屏 · 5 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b00-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 5.17 秒 | 14 分 16 秒 | 24.7 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |

### B01

增强工作流：全精度底模，标准加速。

组件：BF16 原始底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B01 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b01-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 17 分 43 秒 | 29.3 GiB | 45.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B01 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b01-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 14 分 40 秒 | 28.3 GiB | 45.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B02

增强工作流：全精度底模，完整加速适配。

组件：BF16 原始底模 · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B02 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b02-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 17 分 28 秒 | 24.0 GiB | 47.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B02 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b02-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 15 分 25 秒 | 23.9 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B03

增强工作流：全精度底模，完整加速适配，参考优先。

组件：BF16 原始底模（参考生视频版） · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B03 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b03-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 19 分 04 秒 | 24.0 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B03 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b03-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 14 分 49 秒 | 23.9 GiB | 46.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B04

增强工作流：全精度底模，高速。

组件：BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B04 · 768p 竖屏 · 5 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b04-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 5.17 秒 | 8 分 06 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |
| [B04 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b04-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 15 分 32 秒 | 29.3 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B04 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b04-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 25 秒 | 23.9 GiB | 46.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B05

增强工作流：全精度底模，高速，参考优先。

组件：BF16 原始底模（参考生视频版） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B05 · 768p 横屏 · 15 秒 · 种子 42 · 对照运行](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b05-control-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 16 分 34 秒 | 29.3 GiB | 45.4 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B05 · 768p 竖屏 · 15 秒 · 种子 42 · 对照运行](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b05-control-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 13 分 22 秒 | 23.9 GiB | 46.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B05 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b05-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 15 分 43 秒 | 29.3 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b05-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 13 分 10 秒 | 23.9 GiB | 46.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B06

增强工作流：全精度底模，快速。

组件：BF16 原始底模 · 加速 LoRA（turbo 完整版） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B06 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b06-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 13 分 49 秒 | 26.2 GiB | 45.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B06 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b06-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 10 分 55 秒 | 23.9 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B07

增强工作流：电影感与动作连贯。

组件：BF16 原始底模 · 加速 LoRA（turbo 完整版） · 其他 LoRA（电影感、动作连续性修复） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B07 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b07-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 16 分 04 秒 | 26.2 GiB | 46.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B07 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b07-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 14 分 43 秒 | 23.9 GiB | 46.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B08

增强工作流：电影感，高速。

组件：BF16 原始底模 · 加速 LoRA（turbo 与另一种） · 其他 LoRA（电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B08 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b08-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 9 分 16 秒 | 28.0 GiB | 45.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B08 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b08-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 7 分 37 秒 | 23.7 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B09

增强工作流：动作戏，徒手打斗。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（徒手打斗、打斗动作、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B09 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b09-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 14 分 22 秒 | 29.3 GiB | 45.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B09 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b09-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 10 分 19 秒 | 23.9 GiB | 46.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B10

增强工作流：动作戏，武术动作。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（武术动作、打斗动作、动作连续性修复、武术空间物理） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B10 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b10-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 12 分 34 秒 | 29.3 GiB | 45.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B10 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b10-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 22 秒 | 23.9 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B11

增强工作流：动作戏，动作节奏与冲击感。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（动作与打斗推理、兵器速度、冲击反馈、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B11 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b11-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 17 分 52 秒 | 29.3 GiB | 46.4 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B11 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b11-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 11 分 01 秒 | 23.9 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B12

增强工作流：人物动作、镜头运动与口型。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（动作增强、镜头运动、面部表情与口型、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B12 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b12-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 9 分 43 秒 | 28.3 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B12 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b12-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 28 秒 | 23.9 GiB | 47.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B13

增强工作流：写实人物与电影质感。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（写实人物、写实度调节、电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B13 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b13-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 14 分 01 秒 | 29.3 GiB | 45.5 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B13 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b13-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 28 秒 | 23.9 GiB | 46.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B14

增强工作流：高速，细节增强。

组件：BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B14 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b14-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 13 分 55 秒 | 29.3 GiB | 45.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B14 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b14-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 22 秒 | 23.9 GiB | 46.8 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B15

增强工作流：高速，精简加速。

组件：BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B15 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b15-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 11 分 55 秒 | 29.3 GiB | 46.2 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B15 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b15-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 19 秒 | 23.9 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B16

增强工作流：社区热门风格。

组件：BF16 原始底模 · 加速 LoRA（turbo） · 其他 LoRA（社区风格） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B16 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b16-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 9 分 49 秒 | 28.3 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B16 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b16-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 25 秒 | 23.9 GiB | 46.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B17

增强工作流：高速，稳定加速。

组件：BF16 原始底模 · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B17 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b17-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 12 分 04 秒 | 29.3 GiB | 46.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B17 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-b17-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 9 分 31 秒 | 23.9 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B54

测试编号：原镜像 A05 链路在 kLLM 中的原样复现（剪枝 INT8 底模，加速与 EasyCache），用于检验与原镜像的一致性。

组件：INT8 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B54 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b54-landscape-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 9 分 21 秒 | 23.2 GiB | 49.5 GiB | NVIDIA RTX 4080 32 GB |
| [B54 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b54-portrait-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 9 分 26 秒 | 23.2 GiB | 49.9 GiB | NVIDIA RTX 4080 32 GB |
| [B54 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b54-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 10 分 46 秒 | 28.5 GiB | 53.0 GiB | NVIDIA RTX 4080 32 GB |

### B55

原始 BF16 底模，不加速，作为全精度参照。

组件：BF16 原始底模 · 不使用 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · BF16 文本编码器 · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B55 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc3-b55-landscape-s42.mp4) | B55 与原镜像对照（0.2.9-rc.3） | 1344×768 | 15.08 秒 | 25 分 56 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [B55 · 768p 横屏 · 15 秒 · 种子 262347795642618](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc3-b55-landscape-seed2.mp4) | B55 与原镜像对照（0.2.9-rc.3） | 1344×768 | 15.08 秒 | 30 分 59 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [B55 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc3-b55-portrait-s42.mp4) | B55 与原镜像对照（0.2.9-rc.3） | 768×1344 | 15.08 秒 | 26 分 46 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [B55 · 768p 竖屏 · 15 秒 · 种子 262347795642618](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc3-b55-portrait-seed2.mp4) | B55 与原镜像对照（0.2.9-rc.3） | 768×1344 | 15.08 秒 | 27 分 53 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### B59

剪枝 BF16 底模，采用 A05 同款链路（加速、缓存与两遍生成）。

组件：BF16 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B59 · 768p 横屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b59-landscape-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 13 分 56 秒 | 26.0 GiB | 59.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B59 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b59-landscape-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 16 分 36 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B59 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b59-portrait-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 13 分 56 秒 | 26.0 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B59 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b59-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 14 分 26 秒 | 24.0 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B60

剪枝 BF16 底模，B59 去掉加速的参照配置。

组件：BF16 剪枝底模 · 不使用 LoRA · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 768p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [B60 · 768p 横屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b60-landscape-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 12 分 41 秒 | 24.0 GiB | 59.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B60 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b60-landscape-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 12 分 41 秒 | 24.0 GiB | 60.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B60 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b60-portrait-s20261126-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 12 分 36 秒 | 24.0 GiB | 59.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [B60 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-b60-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 15 分 11 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### B61

剪枝 BF16 底模，B59 生成 768p 后做 2 倍超分辨率（输出 1536×2688 或 2688×1536）。

组件：BF16 剪枝底模 · 加速 LoRA（turbo） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · RelayVSR ×2 超分 · 输出 1536p（由 768p 超分）

暂无已发布样例。

## H 系列

以混合权重为底模。

### H02

混合权重底模，完整加速适配；流程与 B02 相同。

组件：混合权重底模（BF16） · 加速 LoRA（turbo 完整版） · EasyCache · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H02 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h02-768p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1344×768 | 15.08 秒 | 20 分 47 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |
| [H02 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h02-768p-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 18 分 41 秒 | 26.2 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |
| [H02 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h02-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 20 分 56 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |

### H04

混合权重底模，高速；流程与 B04 相同。

组件：混合权重底模（BF16） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H04 · 768p 竖屏 · 5 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h04-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 5.17 秒 | 6 分 46 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |
| [H04 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h04-768p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1344×768 | 15.08 秒 | 11 分 49 秒 | 28.2 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [H04 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h04-768p-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 10 分 40 秒 | 23.9 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [H04 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h04-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 10 分 49 秒 | 26.2 GiB | 60.1 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### H05

混合权重底模，高速，参考优先；流程与 B05 相同。

组件：混合权重底模（BF16） · 加速 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H05 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h05-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 14 分 25 秒 | 23.9 GiB | 57.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### H06

混合权重底模，快速；流程与 B06 相同。

组件：混合权重底模（BF16） · 加速 LoRA（turbo 完整版） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H06 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h06-landscape-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 1344×768 | 15.08 秒 | 10 分 56 秒 | 23.9 GiB | 59.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h06-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 15 分 23 秒 | 29.3 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h06-portrait-s42-02.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 15 分 07 秒 | 29.3 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h06-portrait-s42-03.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 15 分 21 秒 | 29.3 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 42 · 新编码](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h06-768p-enc2-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 12 分 55 秒 | 29.3 GiB | 60.1 GiB | NVIDIA RTX 4080 32 GB |
| [H06 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h06-768p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1344×768 | 15.08 秒 | 12 分 19 秒 | 23.9 GiB | 53.9 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 20261126](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h06-768p-portrait-s20261126.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 12 分 55 秒 | 23.9 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [H06 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h06-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 14 分 28 秒 | 26.3 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### H08

混合权重底模，电影感，高速；流程与 B08 相同。

组件：混合权重底模（BF16） · 加速 LoRA（turbo 与另一种） · 其他 LoRA（电影感、动作连续性修复） · Sol 稀疏注意力 · 两遍生成（潜空间放大） · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H08 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h08-768p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1344×768 | 15.08 秒 | 8 分 37 秒 | 23.6 GiB | 48.7 GiB | NVIDIA RTX 4080 32 GB |
| [H08 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h08-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 7 分 55 秒 | 23.7 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |

### H55

混合权重底模，不加速；流程与 B55 相同。

组件：混合权重底模（BF16） · 不使用 LoRA · Sol 稀疏注意力 · 两遍生成（潜空间放大） · BF16 文本编码器 · 480p、768p、960p

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [H55 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h55-portrait-s42-01.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 28 分 30 秒 | 27.2 GiB | 60.7 GiB | NVIDIA RTX 4080 32 GB |
| [H55 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-rc4-runs/rc4-h55-portrait-s42-02.mp4) | 0.2.9-rc.4 实测出片 | 768×1344 | 15.08 秒 | 27 分 16 秒 | 27.2 GiB | 60.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [H55 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h55-768p-landscape-s42.mp4) | 下一版本多轮测试（2026-11-26） | 1344×768 | 15.08 秒 | 27 分 56 秒 | 30.2 GiB | 60.0 GiB | NVIDIA RTX 4080 32 GB |
| [H55 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/prerc4-h55-768p-portrait-s42.mp4) | 下一版本多轮测试（2026-11-26） | 768×1344 | 15.08 秒 | 28 分 11 秒 | 30.2 GiB | 60.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |

## 官方工作流

MiniMax H3 官方参考生成视频工作流，在 kLLM 上运行。

### 官方 BF16

MiniMax H3 官方参考生成视频工作流，BF16 全精度权重。

组件：BF16 原始底模（参考生视频版） · 不使用 LoRA · 单遍生成

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [官方 BF16 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-bf16-official-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 24 分 23 秒 | 26.5 GiB | 46.3 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-bf16-official-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 21 分 29 秒 | 23.9 GiB | 46.6 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 480p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-480p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 864×480 | 15.08 秒 | 8 分 06 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 480p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-480p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 480×864 | 15.08 秒 | 8 分 46 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 720p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-720p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1280×736 | 15.08 秒 | 19 分 30 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 720p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-720p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 736×1280 | 15.08 秒 | 19 分 14 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 21 分 39 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-bf16-official-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 21 分 50 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 480p 横屏 · 5 秒 · 种子 42 · 复核运行](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-bf16-official-480p-landscape-5s-check.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 864×480 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 15 秒 · 种子 42 · 重跑，热态](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-bf16-official-768p-landscape-15s-rerun.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 15.08 秒 | 21 分 48 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-bf16-official-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 5 秒 · 种子 42 · 首次运行](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-bf16-official-768p-landscape-5s-first.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 5 秒 · 种子 42 · 调用说明样例，含 161.0 秒档位切换](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-bf16-official-768p-landscape-5s-sample.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | 12 分 26 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 BF16 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/v028-bf16-official-768p-landscape.mp4) | 0.2.8 调用样例 | 1344×768 | 15.08 秒 | 21 分 35 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |

### 官方 INT8

MiniMax H3 官方参考生成视频工作流，INT8 权重。

组件：INT8 底模（参考生视频版） · 不使用 LoRA · 单遍生成

| 样例 | 样例集 | 分辨率 | 时长 | 耗时 | 显存峰值 | 主机内存峰值 | GPU |
|---|---|---|---|---|---|---|---|
| [官方 INT8 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-int8-official-landscape.mp4) | 全方案样例（0.2.9-rc.2） | 1344×768 | 15.08 秒 | 15 分 10 秒 | 24.4 GiB | 49.0 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc2-int8-official-portrait.mp4) | 全方案样例（0.2.9-rc.2） | 768×1344 | 15.08 秒 | 14 分 25 秒 | 23.2 GiB | 48.7 GiB | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 480p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-480p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 864×480 | 15.08 秒 | 4 分 40 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 480p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-480p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 480×864 | 15.08 秒 | 4 分 55 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 720p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-720p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1280×736 | 15.08 秒 | 12 分 44 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 720p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-720p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 736×1280 | 15.08 秒 | 12 分 42 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-768p-landscape.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 1344×768 | 15.08 秒 | 14 分 30 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 竖屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc11-int8-official-768p-portrait.mp4) | 15 秒交付矩阵（0.2.9-rc.1.1，2026-11-22） | 768×1344 | 15.08 秒 | 14 分 39 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 480p 横屏 · 5 秒 · 种子 42 · 复核运行](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-int8-official-480p-landscape-5s-check.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 864×480 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 15 秒 · 种子 42 · 重跑，热态](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-int8-official-768p-landscape-15s-rerun.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 15.08 秒 | 14 分 27 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求，2 张参考图、1 段音频](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-int8-official-768p-landscape-5s-compact-few.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 5 秒 · 种子 42 · 精简 JSON 请求](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-int8-official-768p-landscape-5s-compact.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | — | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 5 秒 · 种子 42 · 调用说明样例，含 51.5 秒档位切换](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/rc13-int8-official-768p-landscape-5s-sample.mp4) | 接口与交付检查（0.2.9-rc.1.3） | 1344×768 | 5.17 秒 | 5 分 47 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |
| [官方 INT8 · 768p 横屏 · 15 秒 · 种子 42](https://github.com/ANetResearch/ANet-Entertainment/releases/download/kllm-samples/v028-int8-official-768p-landscape.mp4) | 0.2.8 调用样例 | 1344×768 | 15.08 秒 | 14 分 32 秒 | — | — | NVIDIA RTX 4080 SUPER 32 GB |

## 参照输出与早期实测

原镜像 ComfyUI 环境、原样部署与开源框架基线的输出，以及早期引擎与部署实测的样例，见 `samples/manifest.json`（系列 `R` 与 `X`）和对照页面。
