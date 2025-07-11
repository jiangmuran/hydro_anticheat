import csv
import re
from bs4 import BeautifulSoup
import urllib.parse

def parse_record_html(html_file):
    """解析HTML文件并提取记录信息"""
    
    # 读取HTML文件
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到表格
    table = soup.find('table')
    if not table:
        print("未找到表格")
        return []
    
    # 获取表头信息
    headers = []
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            for th in header_row.find_all('th'):
                headers.append(th.get_text(strip=True))
    
    # 获取题目名称（从表头中提取）
    problem_names = []
    for header in headers:
        if header.startswith('#') and ' ' in header:
            # 提取题目名称，去掉#序号
            problem_name = header.split(' ', 1)[1] if ' ' in header else header
            problem_names.append(problem_name)
    
    # 解析表格数据
    records = []
    tbody = table.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 7:  # 确保有足够的列
                # 提取基本信息
                rank = cells[0].get_text(strip=True)
                username = cells[1].get_text(strip=True)
                email = cells[2].get_text(strip=True)
                school = cells[3].get_text(strip=True)
                name = cells[4].get_text(strip=True)
                student_id = cells[5].get_text(strip=True)
                total_score = cells[6].get_text(strip=True)
                
                # 提取题目记录链接
                problem_records = []
                for i in range(7, min(7 + len(problem_names), len(cells))):
                    cell = cells[i]
                    link = cell.find('a')
                    if link:
                        href = link.get('href', '')
                        score_span = link.find('span')
                        score = score_span.get_text(strip=True) if score_span else ''
                        problem_records.append({
                            'problem_name': problem_names[i-7] if i-7 < len(problem_names) else f'Problem_{i-6}',
                            'link': href,
                            'score': score
                        })
                    else:
                        # 没有链接的情况
                        problem_records.append({
                            'problem_name': problem_names[i-7] if i-7 < len(problem_names) else f'Problem_{i-6}',
                            'link': '',
                            'score': ''
                        })
                
                # 创建记录
                record = {
                    'rank': rank,
                    'username': username,
                    'email': email,
                    'school': school,
                    'name': name,
                    'student_id': student_id,
                    'total_score': total_score,
                    'problem_records': problem_records
                }
                records.append(record)
    
    return records

def save_to_csv(records, output_file):
    """将记录保存为CSV文件"""
    
    # 准备CSV数据
    csv_data = []
    
    for record in records:
        # 基础信息
        base_row = {
            '排名': record['rank'],
            '用户名': record['username'],
            '邮箱': record['email'],
            '学校': record['school'],
            '姓名': record['name'],
            '学号': record['student_id'],
            '总分数': record['total_score']
        }
        
        # 添加题目记录
        for prob_record in record['problem_records']:
            problem_name = prob_record['problem_name']
            base_row[f'{problem_name}_分数'] = prob_record['score']
            base_row[f'{problem_name}_链接'] = prob_record['link']
        
        csv_data.append(base_row)
    
    # 写入CSV文件
    if csv_data:
        fieldnames = csv_data[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"数据已保存到 {output_file}")
        print(f"共处理了 {len(records)} 条记录")
    else:
        print("没有找到任何记录")

def main():
    """主函数"""
    input_file = 'record.html'
    output_file = 'records.csv'
    
    try:
        # 解析HTML文件
        print("正在解析HTML文件(record.html)...")
        records = parse_record_html(input_file)
        
        if records:
            # 保存为CSV
            print("正在保存为CSV文件...")
            save_to_csv(records, output_file)
            
            # 显示统计信息
            print("\n统计信息:")
            print(f"总记录数: {len(records)}")
            
            # 统计题目数量
            if records:
                problem_count = len(records[0]['problem_records'])
                print(f"题目数量: {problem_count}")
                
                # 显示题目名称
                if records[0]['problem_records']:
                    print("题目列表:")
                    for i, prob in enumerate(records[0]['problem_records'], 1):
                        print(f"  {i}. {prob['problem_name']}")
        else:
            print("未找到任何记录")
            
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    main() 