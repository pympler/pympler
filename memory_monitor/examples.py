"""
Pympler Memory Monitor 使用示例

展示如何无侵入地集成内存监控服务到现有应用中。
"""

import time
import threading
from typing import List


class ExampleApp:
    def __init__(self):
        self.data: List[str] = []
        self.cache = {}
    
    def add_data(self, count: int = 1000):
        for i in range(count):
            self.data.append(f"data_item_{i}_{time.time()}")
        print(f"已添加 {count} 条数据，当前总数: {len(self.data)}")
    
    def add_to_cache(self, key: str, value: str):
        self.cache[key] = value
        print(f"已缓存: {key}")
    
    def process_data(self):
        temp_list = []
        for i in range(1000):
            temp_list.append({
                "index": i,
                "value": f"processed_{i}",
                "timestamp": time.time()
            })
        return temp_list
    
    def run_loop(self):
        while True:
            self.add_data(100)
            self.process_data()
            time.sleep(1)


def example_1_simple_start():
    """
    示例1: 最简单的启动方式 - 阻塞当前线程
    
    适用场景: 脚本测试、调试阶段
    """
    from memory_monitor import start_monitor
    
    print("=" * 60)
    print("示例1: 简单启动方式 (阻塞模式)")
    print("=" * 60)
    print("\n即将启动内存监控服务...")
    print("服务地址: http://localhost:8080")
    print("API文档: http://localhost:8080/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    start_monitor(host="localhost", port=8080)


def example_2_background_start():
    """
    示例2: 后台启动方式 - 不阻塞主线程
    
    适用场景: 集成到现有Web应用、长期运行的服务
    """
    from memory_monitor import start_monitor_in_background
    
    print("=" * 60)
    print("示例2: 后台启动方式 (非阻塞模式)")
    print("=" * 60)
    
    app = ExampleApp()
    
    print("\n正在后台启动内存监控服务...")
    monitor_thread = start_monitor_in_background(host="localhost", port=8080)
    
    print("内存监控服务已在后台启动!")
    print("服务地址: http://localhost:8080")
    print("API文档: http://localhost:8080/docs")
    
    print("\n开始模拟业务操作...\n")
    
    try:
        for i in range(10):
            print(f"--- 第 {i+1} 轮操作 ---")
            app.add_data(500)
            app.add_to_cache(f"key_{i}", f"value_{i}_{time.time()}")
            processed = app.process_data()
            print(f"处理了 {len(processed)} 条数据")
            time.sleep(2)
            print()
    except KeyboardInterrupt:
        print("\n用户中断操作")
    
    print("\n示例运行完成，监控服务仍在后台运行")
    print("按 Ctrl+C 退出程序\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序已退出")


def example_3_programmatic_api():
    """
    示例3: 程序化API调用方式
    
    适用场景: 在代码中手动控制快照、分析等操作
    """
    from memory_monitor import monitor_server
    
    print("=" * 60)
    print("示例3: 程序化API调用")
    print("=" * 60)
    
    app = ExampleApp()
    
    print("\n1. 创建初始快照...")
    snapshot1 = monitor_server.create_snapshot("initial")
    print(f"   快照ID: {snapshot1.snapshot_id}")
    print(f"   对象总数: {snapshot1.total_objects}")
    print(f"   总大小: {snapshot1.total_size_formatted}")
    
    print("\n2. 执行一些操作...")
    app.add_data(1000)
    app.add_to_cache("test_key", "test_value")
    
    print("\n3. 创建操作后快照...")
    snapshot2 = monitor_server.create_snapshot("after_operations")
    print(f"   快照ID: {snapshot2.snapshot_id}")
    print(f"   对象总数: {snapshot2.total_objects}")
    print(f"   总大小: {snapshot2.total_size_formatted}")
    
    print("\n4. 比较两个快照...")
    diff = monitor_server.compare_snapshots("initial", "after_operations")
    print(f"   对象变化: {diff['diff']['total_objects_diff']}")
    print(f"   内存变化: {diff['diff']['total_size_diff_formatted']}")
    
    print("\n5. 获取对象统计...")
    stats = monitor_server.get_object_stats(limit=5)
    print("   前5种内存占用最大的类型:")
    for stat in stats:
        print(f"   - {stat.type_name}: {stat.count}个对象, {stat.total_size_formatted}")
    
    print("\n6. 导出快照为JSON...")
    filepath = monitor_server.export_to_json(snapshot2, "example_snapshot")
    print(f"   已导出到: {filepath}")
    
    print("\n7. 初始化泄漏检测器...")
    leak_analysis1 = monitor_server.analyze_leaks()
    print(f"   状态: {leak_analysis1.status}")
    
    print("\n8. 执行更多操作后检测泄漏...")
    for i in range(5):
        app.add_data(200)
    
    leak_analysis2 = monitor_server.analyze_leaks()
    print(f"   状态: {leak_analysis2.status}")
    print(f"   潜在泄漏数: {len(leak_analysis2.potential_leaks)}")
    if leak_analysis2.recommendations:
        print("   建议:")
        for rec in leak_analysis2.recommendations:
            print(f"   - {rec}")
    
    print("\n9. 获取进程信息...")
    proc_info = monitor_server.get_process_info()
    print(f"   PID: {proc_info.pid}")
    print(f"   RSS: {proc_info.rss_formatted}")
    print(f"   VSZ: {proc_info.vsz_formatted}")
    
    print("\n" + "=" * 60)
    print("示例3完成!")
    print("=" * 60)


def example_4_combined_usage():
    """
    示例4: 综合使用 - 实际项目中的典型用法
    
    适用场景: 在实际项目中集成内存监控
    """
    from memory_monitor import start_monitor_in_background, monitor_server
    
    print("=" * 60)
    print("示例4: 综合使用 - 实际项目集成示例")
    print("=" * 60)
    
    print("\n[配置] 启动内存监控服务...")
    monitor_thread = start_monitor_in_background(
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
    
    print("[信息] 监控服务已启动: http://localhost:8080")
    print("[信息] API文档: http://localhost:8080/docs")
    
    app = ExampleApp()
    
    def periodic_snapshot():
        count = 0
        while True:
            count += 1
            snapshot = monitor_server.create_snapshot(f"periodic_{count}")
            print(f"\n[定时快照] #{count}: {snapshot.total_size_formatted}")
            
            if count % 3 == 0:
                leak_analysis = monitor_server.analyze_leaks()
                if leak_analysis.potential_leaks:
                    print(f"[警告] 检测到潜在泄漏: {len(leak_analysis.potential_leaks)} 项")
                    for rec in leak_analysis.recommendations:
                        print(f"   - {rec}")
            
            time.sleep(10)
    
    print("\n[启动] 定时快照线程...")
    snapshot_thread = threading.Thread(target=periodic_snapshot, daemon=True)
    snapshot_thread.start()
    
    print("[运行] 主业务循环...\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"--- 业务迭代 {iteration} ---")
            
            app.add_data(300)
            
            temp_data = app.process_data()
            print(f"处理数据: {len(temp_data)} 条")
            
            if iteration % 5 == 0:
                filepath = monitor_server.export_to_json(
                    monitor_server.create_snapshot(f"checkpoint_{iteration}"),
                    f"checkpoint_{iteration}"
                )
                print(f"已导出检查点: {filepath}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n[停止] 用户中断，正在执行最终分析...")
        
        final_snapshot = monitor_server.create_snapshot("final")
        final_file = monitor_server.export_to_json(final_snapshot, "final_analysis")
        print(f"[完成] 最终分析已保存到: {final_file}")
        print("\n[退出] 程序结束")


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Pympler Memory Monitor 使用示例")
    print("=" * 60)
    print("\n请选择要运行的示例:")
    print("  1. 简单启动方式 (阻塞模式)")
    print("  2. 后台启动方式 (非阻塞模式)")
    print("  3. 程序化API调用")
    print("  4. 综合使用 - 实际项目集成示例")
    print("  5. 列出所有API接口")
    print()
    
    choice = input("请输入选择 (1-5): ").strip()
    
    if choice == "1":
        example_1_simple_start()
    elif choice == "2":
        example_2_background_start()
    elif choice == "3":
        example_3_programmatic_api()
    elif choice == "4":
        example_4_combined_usage()
    elif choice == "5":
        print("\n" + "=" * 60)
        print("API 接口列表")
        print("=" * 60)
        print("""
进程信息:
  GET /api/process          - 获取当前进程内存信息

快照管理:
  POST /api/snapshot        - 创建内存快照
  GET  /api/snapshots       - 列出所有快照
  GET  /api/snapshot/{id}   - 获取指定快照详情
  GET  /api/compare         - 比较两个快照 (参数: snap1, snap2)

对象统计:
  GET  /api/stats           - 获取对象统计 (参数: limit)

泄漏分析:
  GET  /api/leaks           - 执行泄漏分析
  POST /api/reset           - 重置泄漏检测器

导出功能:
  POST /api/export/snapshot/{id}  - 导出指定快照
  POST /api/export/current        - 导出当前状态
  GET  /api/exports               - 列出所有导出文件
  GET  /api/exports/{filename}    - 下载导出文件

Web界面:
  GET  /                       - 主页面
  GET  /docs                   - API文档 (Swagger UI)
  GET  /redoc                  - API文档 (ReDoc)
  GET  /openapi.json           - OpenAPI schema
""")
    else:
        print("无效选择，退出程序")
        sys.exit(1)
