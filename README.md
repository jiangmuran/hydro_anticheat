# 全自动下载Hydro比赛选手代码并进行反作弊检测

## 功能介绍
- **支持批量下载选手代码**
- **支持序列相似度、TF-IDF相似度、变量相似度、函数相似度、结构相似度**
- **支持结构化显示，查询指定用户信息**
- **支持识别并标记特殊关键词（如注释、freopen）**
- **支持展示抄袭关系网**

## 文件说明
```
parse_records.py 将导出的html成绩表转换为csv格式

download_codes_auto.py 根据csv格式的成绩表下载选手代码（需填写cookie）

plagiarism_detector.py [比赛名] 计算相似度并导出数据
```

## 使用教程
1. 下载代码并安装依赖
2. 在已经完成的比赛页面点击比赛成绩表->导出为html
3. 将下载的html文件放在同目录并改名为`reports.html`
4. 运行`parse_records.py`转换格式
5. 运行`download_codes_auto.py`爬取选手代码并设定比赛名称
6. 运行`plagiarism_detector.py [比赛名]`进行反作弊检查
7. 打开[可视化链接](https://jiangmuran.com/applications/hydro_anticheat)并上传`result/[比赛名]/[比赛名]_plagiarism_data.json`
8. 报告生成在`result/[比赛名]/[比赛名]_plagiarism_report.txt`

## 免责声明
本系统由jiangmuran开发，采用mit开源协议，任何对于此系统的使用、修改、分享均需注明原作者信息。本人**不承担任何使用此系统的后果及法律责任**。
