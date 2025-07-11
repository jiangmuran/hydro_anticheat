import csv
import requests
import time
import os
import re
import gzip

class AutoCodeDownloader:
    def __init__(self, contest_name):
        """初始化下载器，自动读取cookie文件"""
        self.session = requests.Session()
        self.contest_name = contest_name
        self.setup_session()
        
    def setup_session(self):
        """设置会话和认证"""
        # 设置基本请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 读取cookie文件
        cookie_file = 'cookie.txt'
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_string = f.read().strip()
                
                # 解析cookie
                cookies = {}
                for item in cookie_string.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
                
                # 设置cookie
                self.session.cookies.update(cookies)
                print(f"✓ 已从 {cookie_file} 读取cookie")
                
            except Exception as e:
                print(f"✗ 读取cookie文件失败: {e}")
                return False
        else:
            print(f"✗ 找不到cookie文件: {cookie_file}")
            return False
        
        return True
    
    def create_directory_structure(self):
        """创建目录结构"""
        # 创建result目录
        result_dir = 'result'
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        
        # 创建比赛目录
        contest_dir = os.path.join(result_dir, self.contest_name)
        if not os.path.exists(contest_dir):
            os.makedirs(contest_dir)
        
        return contest_dir
    
    def get_response_text(self, response):
        """获取响应的文本内容，处理压缩"""
        try:
            # 检查内容编码
            content_encoding = response.headers.get('content-encoding', '')
            
            if 'gzip' in content_encoding:
                # 解压gzip内容
                decompressed = gzip.decompress(response.content)
                return decompressed.decode('utf-8')
            elif 'deflate' in content_encoding:
                # 解压deflate内容
                import zlib
                decompressed = zlib.decompress(response.content)
                return decompressed.decode('utf-8')
            else:
                # 直接解码
                return response.text
        except Exception as e:
            print(f"  警告: 解码响应内容时出错 - {e}")
            # 尝试直接解码
            try:
                return response.content.decode('utf-8', errors='ignore')
            except:
                return response.content.decode('latin-1', errors='ignore')
    
    def extract_code_from_html(self, html_content):
        """从HTML中提取代码"""
        # 使用正则表达式查找代码块
        # 查找 <code class="language-xxx"> 到 </code> 之间的内容
        code_pattern = r'<code[^>]*class="[^"]*language-[^"]*"[^>]*>(.*?)</code>'
        match = re.search(code_pattern, html_content, re.DOTALL)
        
        if match:
            code_html = match.group(1)
            # 移除HTML标签，保留纯文本
            code_text = re.sub(r'<[^>]+>', '', code_html)
            # 解码HTML实体
            import html
            code_text = html.unescape(code_text)
            return code_text
        
        # 备用方法：查找 <pre class="line-numbers"> 中的代码
        pre_pattern = r'<pre[^>]*class="[^"]*line-numbers[^"]*"[^>]*>(.*?)</pre>'
        match = re.search(pre_pattern, html_content, re.DOTALL)
        
        if match:
            pre_content = match.group(1)
            # 查找其中的code标签
            code_match = re.search(r'<code[^>]*>(.*?)</code>', pre_content, re.DOTALL)
            if code_match:
                code_html = code_match.group(1)
                code_text = re.sub(r'<[^>]+>', '', code_html)
                import html
                code_text = html.unescape(code_text)
                return code_text
        
        return None
    
    def get_language_from_html(self, html_content):
        """从HTML中提取编程语言"""
        # 查找语言信息
        lang_pattern = r'<code[^>]*class="[^"]*language-([^"]*)"[^>]*>'
        match = re.search(lang_pattern, html_content)
        
        if match:
            return match.group(1)
        
        # 从页面信息中查找语言
        lang_info_pattern = r'<dt[^>]*>语言</dt>\s*<dd[^>]*>([^<]+)</dd>'
        match = re.search(lang_info_pattern, html_content)
        
        if match:
            return match.group(1).strip()
        
        return 'unknown'
    
    def download_code(self, url, username, problem_name, score, contest_dir):
        """下载单个代码文件"""
        try:
            print(f"正在下载: {username} - {problem_name} ({score}分)")
            
            # 发送请求
            response = self.session.get(url, timeout=30)
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"  错误: HTTP状态码 {response.status_code}")
                return None
            
            # 获取响应文本（处理压缩）
            html_content = response.text
            
            # 检查是否包含预期的HTML内容
            if '<html' not in html_content:
                print(f"  警告: 响应内容可能不是HTML页面")
                print(f"  响应长度: {len(html_content)} 字符")
                return None
            
            # 检查是否需要登录
            #if 'login' in html_content.lower() or '登录' in html_content:
            #    print(f"  错误: 需要登录，请检查cookie是否有效")
            #     return None
            
            # 提取代码
            code = self.extract_code_from_html(html_content)
            if not code:
                print(f"  警告: 无法提取代码")
                # 保存HTML内容用于调试
                debug_file = f"debug_{username}_{problem_name}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"  调试信息已保存到: {debug_file}")
                return None
            
            # 获取语言
            language = self.get_language_from_html(html_content)
            
            # 确定文件扩展名
            ext_map = {
                'cpp': '.cpp',
                'c': '.c',
                'cc': '.cpp',
                'c++': '.cpp',
                'python': '.py',
                'py': '.py',
                'java': '.java',
                'pascal': '.pas',
                'pas': '.pas'
            }
            
            #file_ext = ext_map.get(language.lower(), '.txt')
            file_ext = '.cpp'
            
            # 创建题目目录
            problem_dir = os.path.join(contest_dir, problem_name)
            if not os.path.exists(problem_dir):
                os.makedirs(problem_dir)
            
            # 创建文件名
            safe_username = re.sub(r'[<>:"/\\|?*]', '_', username)
            filename = f"{safe_username}_{score}分{file_ext}"
            filepath = os.path.join(problem_dir, filename)
            
            # 保存代码
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"  成功: {filepath}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"  错误: 网络请求失败 - {e}")
            return None
        except Exception as e:
            print(f"  错误: {e}")
            return None
    
    def download_all_codes(self, csv_file):
        """下载所有代码"""
        downloaded_files = []
        
        # 创建目录结构
        contest_dir = self.create_directory_structure()
        print(f"✓ 已创建目录: {contest_dir}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    username = row['用户名']
                    
                    # 遍历所有题目
                    for key, value in row.items():
                        if key.endswith('_链接') and value.strip():
                            problem_name = key.replace('_链接', '')
                            score_key = f"{problem_name}_分数"
                            score = row.get(score_key, '0')
                            
                            # 下载代码
                            filepath = self.download_code(value, username, problem_name, score, contest_dir)
                            if filepath:
                                downloaded_files.append({
                                    'username': username,
                                    'problem': problem_name,
                                    'score': score,
                                    'filepath': filepath,
                                    'url': value
                                })
                            
                            # 添加延迟避免请求过快
                            time.sleep(0.2)
        
        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
        
        return downloaded_files
    
    def generate_summary(self, downloaded_files):
        """生成下载摘要"""
        summary_file = os.path.join('result', self.contest_name, 'download_summary.txt')
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"代码下载摘要 - {self.contest_name}\n")
            f.write("=" * 50 + "\n\n")
            
            # 按用户分组
            users = {}
            for file_info in downloaded_files:
                username = file_info['username']
                if username not in users:
                    users[username] = []
                users[username].append(file_info)
            
            for username, files in users.items():
                f.write(f"用户: {username}\n")
                f.write("-" * 30 + "\n")
                for file_info in files:
                    f.write(f"  {file_info['problem']}: {file_info['score']}分 -> {os.path.basename(file_info['filepath'])}\n")
                f.write("\n")
            
            f.write(f"\n总计下载: {len(downloaded_files)} 个文件\n")
            f.write(f"保存位置: result/{self.contest_name}/\n")
        
        print(f"下载摘要已保存到: {summary_file}")

def main():
    """主函数"""
    print("代码下载器 (自动版)")
    print("=" * 50)
    
    # 检查CSV文件是否存在
    csv_file = 'records.csv'
    if not os.path.exists(csv_file):
        print(f"错误: 找不到文件 {csv_file}")
        print("请先运行 parse_records.py 生成CSV文件")
        return
    
    # 获取比赛名称
    print("请输入比赛名称:")
    contest_name = input().strip()
    
    if not contest_name:
        print("错误: 请输入有效的比赛名称")
        return
    
    # 创建下载器
    downloader = AutoCodeDownloader(contest_name)
    
    # 检查cookie是否设置成功
    if not downloader.setup_session():
        print("错误: 无法设置cookie，请检查cookie.txt文件")
        return
    
    # 开始下载
    print(f"\n开始下载代码到 result/{contest_name}/...")
    downloaded_files = downloader.download_all_codes(csv_file)
    
    # 生成摘要
    if downloaded_files:
        downloader.generate_summary(downloaded_files)
        print(f"\n下载完成! 共下载了 {len(downloaded_files)} 个文件")
        print(f"文件保存在: result/{contest_name}/")
    else:
        print("\n没有下载到任何文件")

if __name__ == "__main__":
    main() 