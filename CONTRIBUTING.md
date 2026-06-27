# Contributing to PAL

感谢你对 PAL（Physical Abstraction Layer）规范的关注。本文档说明如何参与贡献。

## 贡献方式

### 提案与讨论

- **规范修改**：请先开 Issue 描述你的提案，包括动机和影响的章节
- **新想法**：欢迎在 Discussion 区讨论尚未成熟的想法
- **问题反馈**：如果发现规范中的错误、模糊之处或遗漏，请直接开 Issue

### Pull Request 流程

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b proposal/xxx`)
3. 修改规范文档或参考实现代码
4. 确保改动清晰、有理有据
5. 提交 PR，描述你的改动及其动机
6. 等待 review

### Commit 格式

```
主题: <改动类型>: <简短描述>

改动类型:
  spec:      规范修改
  impl:      参考实现代码
  fix:       错误修复
  docs:      文档改进
  example:   示例代码

示例:
  spec: add MCP integration roadmap
  impl: add core0 spi task implementation
  fix: correct section numbering
  docs: add setup guide for ESP32-S3
```

## 规范修改原则

PAL 规范遵循以下原则，提出修改时请考虑：

1. **最小化** — PAL 的范围是 ESP32 级设备的 AI 路由层 + 执行层。不要将范围扩展到协议栈、Agent 框架或硬件参考设计
2. **向下兼容** — Level 2 的实现必须满足 Level 1 的要求。不要破坏兼容性层级
3. **看得见的简洁** — 如果添加一个功能使规范变得明显复杂，它可能需要放在 Future Work 而不是当前版本
4. **示例用通用场景** — 代码示例使用通用嵌入式场景（传感器、继电器、LED），不绑定特定产品

## 需要帮助的方向

以下领域特别需要社区贡献：

- [ ] **认证与安全**：Agent ↔ 终端之间的 Token/证书认证机制
- [ ] **多终端协调**：一个 Agent 管理多个 PAL 终端的协议扩展
- [ ] **MCP 集成**：将 PAL JSON 协议包装为标准 MCP 工具
- [ ] **OTA 安全**：固件签名验证和安全的 OTA 更新流程
- [ ] **Level 3 冗余策略**：双 MCU 物理隔离的具体实现方案
- [ ] **与 ESP-Claw 的互操作**：PAL 终端注册为 ESP-Claw 工具的方案
- [ ] **参考实现**：Core 0 C 框架和 Core 1 MicroPython 代码
- [ ] **测试套件**：PAL 终端合规性测试工具

## 行为准则

- 尊重所有贡献者
- 建设性讨论，专注于技术和规范本身
- 欢迎不同意见，以理服人
- 中文和英文讨论均欢迎

## 许可

本仓库的规范文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。
参考实现代码（`impl/` 目录）采用 [MIT](https://opensource.org/license/MIT) 许可。
提交 PR 即表示你同意你的贡献在上述许可下发布。
