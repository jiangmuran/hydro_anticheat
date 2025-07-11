#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反抄袭检测程序
检测代码相似度和其他特征，生成详细报告
"""

import os
import re
import hashlib
import difflib
import json
import time
import sys
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class PlagiarismDetector:
    def __init__(self):
        self.results = {}
        self.similarity_matrix = {}
        self.suspicious_pairs = []
        self.special_keywords = ['freopen', 'system', 'exec', 'eval', 'subprocess', '//', '/*', '*/']
        
    def normalize_code(self, code: str) -> str:
        """标准化代码，移除注释、空行、多余空格等"""
        # 移除C++风格注释
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # 移除多余空格和空行
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def extract_features(self, code: str) -> Dict:
        """提取代码特征"""
        normalized_code = self.normalize_code(code)
        
        features = {
            'length': len(normalized_code),
            'lines': len(code.split('\n')),
            'variables': self.extract_variables(normalized_code),
            'functions': self.extract_functions(normalized_code),
            'keywords': self.extract_keywords(normalized_code),
            'structure': self.extract_structure(normalized_code),
            'hash': hashlib.md5(normalized_code.encode()).hexdigest(),
            'normalized_code': normalized_code,
            'special_keywords': self.detect_special_keywords(code)
        }
        
        return features
    
    def extract_variables(self, code: str) -> List[str]:
        """提取变量名"""
        # 匹配变量声明
        var_patterns = [
            r'\b(int|long|double|float|char|bool|string)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\b(vector|map|set|queue|stack)\s*<[^>]*>\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*[=;]\s*'
        ]
        
        variables = set()
        for pattern in var_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if isinstance(match, tuple):
                    variables.update(match)
                else:
                    variables.add(match)
        
        return list(variables)
    
    def extract_functions(self, code: str) -> List[str]:
        """提取函数名"""
        func_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{'
        functions = re.findall(func_pattern, code)
        return functions
    
    def extract_keywords(self, code: str) -> Dict[str, int]:
        """提取关键字频率"""
        keywords = [
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
            'return', 'cin', 'cout', 'printf', 'scanf', 'main', 'include', 'using',
            'namespace', 'std', 'vector', 'map', 'set', 'queue', 'stack', 'struct',
            'class', 'public', 'private', 'protected', 'const', 'static', 'void',
            'int', 'long', 'double', 'float', 'char', 'bool', 'string'
        ]
        
        keyword_count = {}
        for keyword in keywords:
            count = len(re.findall(r'\b' + keyword + r'\b', code, re.IGNORECASE))
            if count > 0:
                keyword_count[keyword] = count
        
        return keyword_count
    
    def extract_structure(self, code: str) -> Dict:
        """提取代码结构特征"""
        structure = {
            'brackets': code.count('{') + code.count('}'),
            'parentheses': code.count('(') + code.count(')'),
            'semicolons': code.count(';'),
            'if_statements': len(re.findall(r'\bif\s*\(', code)),
            'for_loops': len(re.findall(r'\bfor\s*\(', code)),
            'while_loops': len(re.findall(r'\bwhile\s*\(', code)),
            'function_calls': len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(', code))
        }
        return structure
    

    
    def detect_special_keywords(self, code: str) -> Dict[str, List[str]]:
        """检测特殊关键词和注释"""
        detected = {}
        
        # 检测特殊关键词
        for keyword in self.special_keywords:
            if keyword in ['//', '/*', '*/']:
                # 对于注释符号，提取完整的注释内容
                if keyword == '//':
                    # 单行注释
                    comment_lines = re.findall(r'//(.*)$', code, re.MULTILINE)
                    if comment_lines:
                        lines = code.split('\n')
                        keyword_lines = []
                        for i, line in enumerate(lines, 1):
                            if '//' in line:
                                comment_start = line.find('//')
                                comment_content = line[comment_start:].strip()
                                keyword_lines.append(f"第{i}行: {comment_content}")
                        detected['单行注释'] = keyword_lines
                elif keyword == '/*':
                    # 多行注释开始
                    multi_comments = re.findall(r'/\*(.*?)\*/', code, re.DOTALL)
                    if multi_comments:
                        lines = code.split('\n')
                        keyword_lines = []
                        for i, line in enumerate(lines, 1):
                            if '/*' in line or '*/' in line:
                                keyword_lines.append(f"第{i}行: {line.strip()}")
                        detected['多行注释'] = keyword_lines
            else:
                # 其他特殊关键词
                matches = re.findall(rf'\b{keyword}\b', code, re.IGNORECASE)
                if matches:
                    # 获取包含关键词的完整行
                    lines = code.split('\n')
                    keyword_lines = []
                    for i, line in enumerate(lines, 1):
                        if keyword.lower() in line.lower():
                            keyword_lines.append(f"第{i}行: {line.strip()}")
                    detected[keyword] = keyword_lines
        
        return detected
    
    def calculate_similarity(self, code1: str, code2: str) -> float:
        """计算代码相似度"""
        # 使用difflib计算相似度
        similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
        return similarity
    
    def calculate_tfidf_similarity(self, texts: List[str]) -> np.ndarray:
        """使用TF-IDF计算文本相似度"""
        vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(3, 5),
            min_df=1,
            max_df=0.9
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            return similarity_matrix
        except:
            # 如果TF-IDF失败，返回零矩阵
            return np.zeros((len(texts), len(texts)))
    
    def detect_plagiarism(self, contest_name: str) -> Dict:
        """检测抄袭"""
        contest_dir = os.path.join("result", contest_name)
        if not os.path.exists(contest_dir):
            print(f"错误: 比赛目录 {contest_dir} 不存在")
            return {}
        
        print(f"开始检测比赛: {contest_name}")
        
        # 获取所有子目录（题目）
        subdirs = []
        for item in os.listdir(contest_dir):
            subdir_path = os.path.join(contest_dir, item)
            if os.path.isdir(subdir_path):
                subdirs.append(subdir_path)
        
        if not subdirs:
            print(f"在 {contest_dir} 中没有找到题目目录")
            return {}
        
        all_reports = {}
        
        # 检测每个题目
        for subdir in subdirs:
            problem_name = os.path.basename(subdir)
            print(f"检测题目: {problem_name}")
            
            # 获取所有代码文件
            code_files = []
            for root, dirs, files in os.walk(subdir):
                for file in files:
                    if file.endswith('.cpp'):
                        file_path = os.path.join(root, file)
                        code_files.append(file_path)
            
            if not code_files:
                print(f"在 {subdir} 中没有找到代码文件")
                continue
            
            print(f"找到 {len(code_files)} 个代码文件")
            
            # 分析每个文件
            file_features = {}
            file_codes = {}
            
            for file_path in code_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    filename = os.path.basename(file_path)
                    features = self.extract_features(code)
                    file_features[filename] = features
                    file_codes[filename] = features['normalized_code']
                    
                    print(f"分析文件: {filename}")
                    
                except Exception as e:
                    print(f"读取文件 {file_path} 时出错: {e}")
            
            # 计算相似度
            filenames = list(file_codes.keys())
            codes = list(file_codes.values())
            
            # 使用TF-IDF计算相似度
            tfidf_similarity = self.calculate_tfidf_similarity(codes)
            
            # 计算两两之间的相似度
            similarity_pairs = []
            suspicious_pairs = []
            
            for i in range(len(filenames)):
                for j in range(i + 1, len(filenames)):
                    file1, file2 = filenames[i], filenames[j]
                    code1, code2 = codes[i], codes[j]
                    
                    # 多种相似度计算方法
                    sequence_similarity = self.calculate_similarity(code1, code2)
                    tfidf_sim = tfidf_similarity[i][j]
                    
                    # 特征相似度
                    features1 = file_features[file1]
                    features2 = file_features[file2]
                    
                    # 变量名相似度
                    var_similarity = self.calculate_set_similarity(
                        set(features1['variables']), 
                        set(features2['variables'])
                    )
                    
                    # 函数名相似度
                    func_similarity = self.calculate_set_similarity(
                        set(features1['functions']), 
                        set(features2['functions'])
                    )
                    
                    # 结构相似度
                    structure_similarity = self.calculate_structure_similarity(
                        features1['structure'], 
                        features2['structure']
                    )
                    
                    # 综合相似度
                    overall_similarity = (
                        sequence_similarity * 0.4 +
                        tfidf_sim * 0.3 +
                        var_similarity * 0.1 +
                        func_similarity * 0.1 +
                        structure_similarity * 0.1
                    )
                    
                    similarity_info = {
                        'file1': file1,
                        'file2': file2,
                        'sequence_similarity': sequence_similarity,
                        'tfidf_similarity': tfidf_sim,
                        'variable_similarity': var_similarity,
                        'function_similarity': func_similarity,
                        'structure_similarity': structure_similarity,
                        'overall_similarity': overall_similarity
                    }
                    
                    similarity_pairs.append(similarity_info)
                    
                    # 标记可疑的抄袭对
                    if overall_similarity > 0.5:
                        suspicious_pairs.append(similarity_info)
            
            # 生成该题目的报告
            problem_report = {
                'problem_name': problem_name,
                'total_files': len(filenames),
                'file_features': file_features,
                'similarity_pairs': similarity_pairs,
                'suspicious_pairs': suspicious_pairs,
                'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            all_reports[problem_name] = problem_report
        
        # 生成总报告
        report = {
            'contest_name': contest_name,
            'problems': all_reports,
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
    
    def calculate_set_similarity(self, set1: Set, set2: Set) -> float:
        """计算两个集合的相似度"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    def calculate_structure_similarity(self, struct1: Dict, struct2: Dict) -> float:
        """计算结构相似度"""
        if not struct1 or not struct2:
            return 0.0
        
        total_diff = 0
        total_sum = 0
        
        for key in struct1:
            if key in struct2:
                val1, val2 = struct1[key], struct2[key]
                max_val = max(val1, val2)
                if max_val > 0:
                    diff = abs(val1 - val2)
                    total_diff += diff
                    total_sum += max_val
        
        if total_sum == 0:
            return 1.0
        
        return 1.0 - (total_diff / total_sum)
    
    def generate_report(self, report: Dict, contest_name: str):
        """生成详细报告"""
        report_file = os.path.join("result", contest_name, f"{contest_name}_plagiarism_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"反抄袭检测报告 - {contest_name}\n")
            f.write("=" * 80 + "\n")
            f.write(f"检测时间: {report['analysis_time']}\n")
            f.write("=" * 80 + "\n\n")
            
            # 检测特殊关键词
            special_keywords_found = []
            for problem_name, problem_report in report['problems'].items():
                for filename, features in problem_report['file_features'].items():
                    if features['special_keywords']:
                        special_keywords_found.append({
                            'problem': problem_name,
                            'file': filename,
                            'keywords': features['special_keywords']
                        })
            
            if special_keywords_found:
                f.write("🚨 检测到特殊关键词:\n")
                f.write("-" * 50 + "\n")
                for item in special_keywords_found:
                    f.write(f"题目: {item['problem']}\n")
                    f.write(f"文件: {item['file']}\n")
                    for keyword, lines in item['keywords'].items():
                        f.write(f"关键词 '{keyword}' 出现在:\n")
                        for line in lines:
                            f.write(f"  {line}\n")
                    f.write("-" * 30 + "\n")
                f.write("\n")
            
            # 收集所有可疑抄袭对
            all_suspicious_pairs = []
            for problem_name, problem_report in report['problems'].items():
                for pair in problem_report['suspicious_pairs']:
                    pair_with_problem = pair.copy()
                    pair_with_problem['problem'] = problem_name
                    all_suspicious_pairs.append(pair_with_problem)
            
            # 显示所有可疑抄袭对
            if all_suspicious_pairs:
                f.write("🚨 所有可疑抄袭对:\n")
                f.write("-" * 50 + "\n")
                for pair in sorted(all_suspicious_pairs, 
                                 key=lambda x: x['overall_similarity'], reverse=True):
                    f.write(f"题目: {pair['problem']}\n")
                    f.write(f"文件1: {pair['file1']}\n")
                    f.write(f"文件2: {pair['file2']}\n")
                    f.write(f"综合相似度: {pair['overall_similarity']:.3f}\n")
                    f.write(f"序列相似度: {pair['sequence_similarity']:.3f}\n")
                    f.write(f"TF-IDF相似度: {pair['tfidf_similarity']:.3f}\n")
                    f.write(f"变量相似度: {pair['variable_similarity']:.3f}\n")
                    f.write(f"函数相似度: {pair['function_similarity']:.3f}\n")
                    f.write(f"结构相似度: {pair['structure_similarity']:.3f}\n")
                    f.write("-" * 30 + "\n\n")
            else:
                f.write("✅ 未发现可疑抄袭对\n\n")
            
            # 处理每个题目
            for problem_name, problem_report in report['problems'].items():
                f.write(f"📋 题目: {problem_name}\n")
                f.write("=" * 60 + "\n")
                f.write(f"文件总数: {problem_report['total_files']}\n")
                f.write(f"分析时间: {problem_report['analysis_time']}\n\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
            
            # 所有文件特征分析（放在最后）
            f.write("📊 所有文件特征分析:\n")
            f.write("=" * 80 + "\n")
            
            for problem_name, problem_report in report['problems'].items():
                f.write(f"\n📋 题目: {problem_name}\n")
                f.write("-" * 50 + "\n")
                
                for filename, features in problem_report['file_features'].items():
                    f.write(f"\n题目: {problem_name} | 文件: {filename}\n")
                    f.write(f"代码长度: {features['length']} 字符\n")
                    f.write(f"代码行数: {features['lines']} 行\n")
                    f.write(f"变量数量: {len(features['variables'])}\n")
                    f.write(f"函数数量: {len(features['functions'])}\n")
                    
                    if features['variables']:
                        f.write(f"变量列表: {', '.join(features['variables'][:10])}\n")
                    if features['functions']:
                        f.write(f"函数列表: {', '.join(features['functions'][:10])}\n")
                    
                    # 添加特殊关键词和注释检测结果
                    if features['special_keywords']:
                        f.write("⚠️ 检测到特殊关键词和注释:\n")
                        for keyword, lines in features['special_keywords'].items():
                            f.write(f"  {keyword}:\n")
                            for line in lines:
                                f.write(f"    {line}\n")
                    
                    f.write(f"代码哈希: {features['hash']}\n")
                    f.write("-" * 25 + "\n")
        
        print(f"报告已生成: {report_file}")
        
        # 生成JSON格式的详细数据
        json_file = os.path.join("result", contest_name, f"{contest_name}_plagiarism_data.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"详细数据已保存: {json_file}")


def main():
    detector = PlagiarismDetector()
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法: python plagiarism_detector.py <比赛名>")
        print("例如: python plagiarism_detector.py xxxx")
        return
    
    contest_name = sys.argv[1]
    
    # 检测指定的比赛
    print(f"开始检测比赛: {contest_name}")
    report = detector.detect_plagiarism(contest_name)
    
    if report:
        detector.generate_report(report, contest_name)
        print(f"\n反抄袭检测完成！报告已生成在 result/{contest_name}/ 目录下")
    else:
        print("检测失败，请检查比赛名是否正确")


if __name__ == "__main__":
    main() 