# 部署本地QuickForm

QuickForm是一个轻量级表单数据回收系统，专门为大模型生成的交互网页设计，嵌入专用地址后即可实现数据收集、分析与报告生成，专注于提供智能的数据分析和可视化功能。为了降低使用门槛，我们设计了无加密形式的API数据接口，因此QuickForm适用于对安全不敏感的，临时性的教学数据采集工作，如课前调查，课中反馈等。

为了让更多教师最快速度用上QuickForm，体验AI赋能教学带来的各种便利，我们购买云服务器，申请域名，部署了线上的版本（https://quickform.cn/）。但是，我们依然期望更多的老师能自己部署，把QuickForm部署到自己的电脑上，部署到本地服务器上，在局域网中使用。

本地部署QuickForm两种方式，即教师版和校园版。

QuickForm文档地址：https://quickform.readthedocs.io/

QuickForm开源仓库：https://gitee.com/wstlab/quickform

## 部署QuickForm教师版

QuickForm教师版是一个开源软件，适用于每一位教师。老师们只要将QuickForm解压到本地电脑，然后运行bat文件即可，支持Windows、Linux、MacOS等系统。

<!-- mp4格式 -->
<video id="video" controls="" preload="none" poster="封面">
      <source id="mp4" src="../images/guide/QuickForm_t_deploy.mp4" type="video/mp4">
</videos>

下载地址：https://gitee.com/wstlab/quickform/tree/main/teacher

启动QuickForm后，你的电脑就成为一台Web服务器，通过局域网地址即可访问。当然，你也可以通过一些网络软件，将本地端口映射到公网上。或者可以申请一个云服务器部署，但前提是要确保安全。

## 部署QuickForm校园版

QuickForm校园版是一个免费软件，仅面向项目成员开源。和教师版对比，校园版支持多用户，支持群组和交流功能，适合部署在校园内，供所有教师使用。

要获得QuickForm校园版，首先需要与项目组签署一个合作协议。合作协议的核心内容为能定期提供优秀案例分享给更多老师。我们期望能找到志同道合的朋友。

合作介绍：https://mp.weixin.qq.com/s/JIJSxCsL-ImGNuS2UnoAZg

协议内容：QuickForm校园版合作协议（第2版）

如果你有意向加入项目组，请先填写一个简单的问卷。我们将在2026年节后的开学初启动签约工作。

想加入QuickForm项目的意向表：https://wj.qq.com/s2/25715865/17b8/



